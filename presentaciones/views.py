from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse, HttpResponse, Http404
from django.contrib.admin.views.decorators import staff_member_required
from django.utils import timezone
from django.core.paginator import Paginator
from django.http import HttpResponse
from django.shortcuts import render
from django.template.loader import render_to_string
from django.utils import timezone
from encuestas.models import RespuestaEncuesta
from .models import Presentacion, VideoEvento  
from io import BytesIO

def portal_presentaciones(request):
    """Vista principal del portal de presentaciones"""
    presentaciones = Presentacion.objects.filter(activa=True).select_related(
        'administracion'
    ).order_by('orden', 'fecha')
    
    # Cambio: Obtener TODOS los videos activos ordenados
    videos_evento = VideoEvento.objects.filter(activo=True).order_by('orden')
    
    # Estadísticas del evento
    total_presentaciones = presentaciones.count()
    total_participantes = 200  # Esto podría venir de un modelo separado o configuración
    dias_evento = 1
    
    context = {
        'presentaciones': presentaciones,
        'total_presentaciones': total_presentaciones,
        'total_participantes': total_participantes,
        'videos_evento': videos_evento,  # Cambio: videos_evento en lugar de video_bienvenida
        'dias_evento': dias_evento,
    }
    return render(request, 'presentaciones/portal_ppt.html', context)

def api_video_detalle(request, video_id):
    """API para obtener detalles de un video del evento"""
    try:
        video = VideoEvento.objects.get(id=video_id, activo=True)
        
        data = {
            'id': video.id,
            'titulo': video.titulo,
            'descripcion': video.descripcion,
            'video_url': video.video.url if video.video else None,
            'thumbnail_url': video.imagen_thumbnail.url if video.imagen_thumbnail else None,
            'orden': video.orden,
        }
        
        return JsonResponse(data)
    except VideoEvento.DoesNotExist:
        return JsonResponse({'error': 'Video no encontrado'}, status=404)

@staff_member_required
def dashboard_admin(request):
    """Dashboard administrativo para gestión de respuestas"""
    respuestas = RespuestaEncuesta.objects.all().order_by('-creado_en')
    
    # Filtros
    search_query = request.GET.get('search', '')
    if search_query:
        respuestas = respuestas.filter(comentarios__icontains=search_query)
    
    fecha_filter = request.GET.get('fecha', 'all')
    if fecha_filter == 'today':
        respuestas = respuestas.filter(creado_en__date=timezone.now().date())
    elif fecha_filter == 'week':
        respuestas = respuestas.filter(creado_en__date__gte=timezone.now().date() - timedelta(days=7))
    elif fecha_filter == 'month':
        respuestas = respuestas.filter(creado_en__date__gte=timezone.now().date() - timedelta(days=30))
    
    # Paginación
    paginator = Paginator(respuestas, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Estadísticas generales
    total_respuestas = respuestas.count()
    
    # Calcular promedio de calificaciones
    promedios = []
    for respuesta in RespuestaEncuesta.objects.all():
        promedio = respuesta.calificacion_promedio()
        if promedio > 0:
            promedios.append(promedio)
    
    promedio_general = sum(promedios) / len(promedios) if promedios else 0
    
    # Respuestas de hoy
    hoy = timezone.now().date()
    respuestas_hoy = RespuestaEncuesta.objects.filter(creado_en__date=hoy).count()

    # Tasa de completitud
    todas_respuestas = RespuestaEncuesta.objects.all()
    respuestas_completas = sum(1 for r in todas_respuestas if r.esta_completa())
    tasa_completitud = (respuestas_completas / todas_respuestas.count() * 100) if todas_respuestas.count() > 0 else 0

    context = {
        'page_obj': page_obj,
        'respuestas': page_obj.object_list,
        'total_respuestas': total_respuestas,
        'promedio_calificacion': round(promedio_general, 1),
        'respuestas_hoy': respuestas_hoy,
        'tasa_completitud': round(tasa_completitud),
        'filtro_fecha': fecha_filter,
    }
    return render(request, 'presentaciones/dashboard.html', context)

def descargar_presentacion(request, presentacion_id):
    """Descarga de archivos PDF de presentaciones"""
    presentacion = get_object_or_404(Presentacion, id=presentacion_id, activa=True)
    
    if presentacion.archivo_pdf:
        try:
            response = HttpResponse(
                presentacion.archivo_pdf.read(), 
                content_type='application/pdf'
            )
            filename = f"{presentacion.titulo.replace(' ', '_')}.pdf"
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            return response
        except FileNotFoundError:
            raise Http404("Archivo no encontrado")
    else:
        raise Http404("No hay archivo PDF disponible para esta presentación")

def api_presentacion_detalle(request, presentacion_id):
    """API para obtener detalles de una presentación"""
    try:
        presentacion = Presentacion.objects.select_related(
            'administracion'
        ).get(id=presentacion_id, activa=True)
        
        data = {
            'id': presentacion.id,
            'titulo': presentacion.titulo,
            'ponente': presentacion.ponente,
            'administracion': presentacion.administracion.nombre,
            'fecha': presentacion.fecha.strftime('%d de %B, %Y'),
            'duracion': presentacion.duracion_minutos,
            'descripcion': presentacion.descripcion,
            'tiene_pdf': bool(presentacion.archivo_pdf),
        }
        
        return JsonResponse(data)
    except Presentacion.DoesNotExist:
        return JsonResponse({'error': 'Presentación no encontrada'}, status=404)

@staff_member_required
def exportar_informe_pdf(request):
    """Generar y DESCARGAR PDF directamente usando ReportLab con porcentajes por evaluación"""
    try:
        from reportlab.lib.pagesizes import letter, A4
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib import colors
        from reportlab.lib.units import inch
        from collections import Counter
        
        # Obtener TODAS las respuestas
        respuestas = RespuestaEncuesta.objects.all().order_by('-creado_en')
        total_respuestas = respuestas.count()
        
        # Estadísticas básicas
        stats = {
            'total_respuestas': total_respuestas,
            'respuestas_completas': sum(1 for r in respuestas if r.esta_completa()),
            'respuestas_con_comentarios': respuestas.filter(comentarios__isnull=False).exclude(comentarios='').count(),
            'promedio_general': sum(r.calificacion_promedio() for r in respuestas if r.calificacion_promedio() > 0) / total_respuestas if total_respuestas > 0 else 0,
        }
        
        # NUEVO: Calcular porcentajes por cada sección
        def calcular_porcentajes_seccion(campo_evaluacion):
            """Calcula los porcentajes para una sección específica"""
            evaluaciones = [getattr(r, campo_evaluacion) for r in respuestas if getattr(r, campo_evaluacion)]
            contador = Counter(evaluaciones)
            total_evaluaciones = len(evaluaciones)
            
            porcentajes = {}
            opciones = ['muy_buena', 'buena', 'regular', 'mala', 'incompleta']
            nombres_opciones = {
                'muy_buena': 'Muy Buena',
                'buena': 'Buena', 
                'regular': 'Regular',
                'mala': 'Mala',
                'incompleta': 'Incompleta'
            }
            
            for opcion in opciones:
                cantidad = contador.get(opcion, 0)
                porcentaje = (cantidad / total_evaluaciones * 100) if total_evaluaciones > 0 else 0
                porcentajes[nombres_opciones[opcion]] = {
                    'cantidad': cantidad,
                    'porcentaje': porcentaje
                }
            
            return porcentajes, total_evaluaciones
        
        # Calcular porcentajes para todas las secciones
        secciones_stats = {}
        secciones = {
            'ADFAN': 'evaluacion_adfan',
            'ACUDEN': 'evaluacion_acuden', 
            'ADSEF': 'evaluacion_adsef',
            'ASUME': 'evaluacion_asume',
            'Secretariado': 'evaluacion_secretariado'
        }
        
        for nombre_seccion, campo in secciones.items():
            porcentajes, total_eval = calcular_porcentajes_seccion(campo)
            secciones_stats[nombre_seccion] = {
                'porcentajes': porcentajes,
                'total_evaluaciones': total_eval
            }
        
        # Crear PDF en memoria con márgenes mínimos
        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer, 
            pagesize=A4, 
            rightMargin=20,
            leftMargin=20, 
            topMargin=72, 
            bottomMargin=40
        )
        
        # Estilos
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=18,
            spaceAfter=30,
            textColor=colors.HexColor('#1c2854'),
            alignment=1
        )
        
        subtitle_style = ParagraphStyle(
            'CustomSubtitle',
            parent=styles['Normal'],
            fontSize=12,
            spaceAfter=20,
            textColor=colors.HexColor('#7f8c8d'),
            alignment=1
        )
        
        # Contenido del PDF
        story = []
        
        # Título
        story.append(Paragraph("INFORME DE EVALUACIÓN DE PRESENTACIONES", title_style))
        story.append(Paragraph("Departamento de la Familia de Puerto Rico", subtitle_style))
        story.append(Paragraph(f"Generado el {timezone.now().strftime('%d de %B, %Y a las %H:%M')}", subtitle_style))
        story.append(Spacer(1, 20))
        
        # Estadísticas generales
        stats_data = [
            ['Concepto', 'Cantidad'],
            ['Total de Respuestas', str(stats['total_respuestas'])],
            ['Respuestas Completas', str(stats['respuestas_completas'])],
            ['Con Comentarios', str(stats['respuestas_con_comentarios'])],
            ['Promedio General', f"{stats['promedio_general']:.1f}"],
        ]
        
        stats_table = Table(stats_data, colWidths=[3*inch, 1.5*inch])
        stats_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1c2854')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(stats_table)
        story.append(Spacer(1, 30))
        
        # NUEVA SECCIÓN: Análisis de porcentajes por sección
        story.append(Paragraph("ANÁLISIS DETALLADO POR SECCIÓN", styles['Heading2']))
        story.append(Spacer(1, 15))
        
        for nombre_seccion, datos in secciones_stats.items():
            # Título de la sección
            story.append(Paragraph(f"Sección: {nombre_seccion}", styles['Heading3']))
            story.append(Paragraph(f"Total de evaluaciones: {datos['total_evaluaciones']}", styles['Normal']))
            story.append(Spacer(1, 10))
            
            # Crear tabla de porcentajes para esta sección
            porcentajes_data = [['Calificación', 'Cantidad', 'Porcentaje']]
            
            for calificacion, info in datos['porcentajes'].items():
                if info['cantidad'] > 0:  # Solo mostrar opciones que tienen respuestas
                    porcentajes_data.append([
                        calificacion,
                        str(info['cantidad']),
                        f"{info['porcentaje']:.1f}%"
                    ])
            
            # Si no hay datos, mostrar mensaje
            if len(porcentajes_data) == 1:
                porcentajes_data.append(['Sin evaluaciones', '0', '0%'])
            
            porcentajes_table = Table(porcentajes_data, colWidths=[2*inch, 1*inch, 1*inch])
            porcentajes_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#34495e')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('FONTSIZE', (0, 1), (-1, -1), 9),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
                ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8f9fa')]),
                ('GRID', (0, 0), (-1, -1), 0.75, colors.grey),
                ('TOPPADDING', (0, 1), (-1, -1), 4),
                ('BOTTOMPADDING', (0, 1), (-1, -1), 4),
            ]))
            
            story.append(porcentajes_table)
            story.append(Spacer(1, 15))
        
        # Nueva página para el listado completo
        story.append(PageBreak())
        story.append(Paragraph("LISTADO COMPLETO DE RESPUESTAS", styles['Heading2']))
        story.append(Spacer(1, 12))
        
        # Función para crear tabla con todas las respuestas
        def crear_tabla_respuestas(respuestas_list):
            table_data = [['Fecha', 'ADFAN', 'ACUDEN', 'ADSEF', 'ASUME', 'Secretariado', 'Comentarios']]
            
            for respuesta in respuestas_list:
                def get_full_display(evaluation):
                    if not evaluation:
                        return '-'
                    mapping = {
                        'muy_buena': 'Muy Buena',
                        'buena': 'Buena',
                        'regular': 'Regular',
                        'mala': 'Mala',
                        'incompleta': 'Incompleta'
                    }
                    return mapping.get(evaluation, evaluation.title())
                
                comentarios_texto = ''
                if respuesta.comentarios and respuesta.comentarios.strip():
                    comentarios_raw = respuesta.comentarios.strip()
                    comentarios_raw = comentarios_raw.replace('\n', '<br/>')
                    comentarios_raw = comentarios_raw.replace('\r', '')
                    comment_style = ParagraphStyle(
                        'CommentStyle',
                        fontSize=8,
                        leading=10,
                        leftIndent=3,
                        rightIndent=3,
                        spaceAfter=0,
                        spaceBefore=0,
                        wordWrap='LTR'
                    )
                    comentarios_texto = Paragraph(comentarios_raw, comment_style)
                else:
                    comentarios_texto = '-'
                
                row = [
                    respuesta.creado_en.strftime('%d/%m/%Y'),
                    get_full_display(respuesta.evaluacion_adfan),
                    get_full_display(respuesta.evaluacion_acuden),
                    get_full_display(respuesta.evaluacion_adsef),
                    get_full_display(respuesta.evaluacion_asume),
                    get_full_display(respuesta.evaluacion_secretariado),
                    comentarios_texto
                ]
                table_data.append(row)
            
            return table_data
        
        # Crear tabla con todas las respuestas
        table_data = crear_tabla_respuestas(respuestas)
        col_widths = [0.8*inch, 0.9*inch, 0.9*inch, 0.9*inch, 0.9*inch, 1.0*inch, 2.2*inch]
        rows_per_table = 18
        
        for i in range(0, len(table_data), rows_per_table):
            if i > 0:
                story.append(PageBreak())
                story.append(Paragraph(f"LISTADO DE RESPUESTAS (Continuación - Página {(i//rows_per_table) + 1})", styles['Heading2']))
                story.append(Spacer(1, 12))
            
            chunk_data = table_data[0:1] + table_data[i+1:i+rows_per_table+1]
            
            responses_table = Table(chunk_data, colWidths=col_widths)
            responses_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#34495e')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 9),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
                ('TOPPADDING', (0, 0), (-1, 0), 6),
                ('LEFTPADDING', (0, 0), (-1, 0), 6),   
                ('RIGHTPADDING', (0, 0), (-1, 0), 6),
                ('ALIGN', (0, 0), (5, -1), 'CENTER'),
                ('ALIGN', (6, 1), (6, -1), 'LEFT'),
                ('FONTSIZE', (0, 1), (5, -1), 8),
                ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8f9fa')]),
                ('GRID', (0, 0), (-1, -1), 0.75, colors.grey),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('LEFTPADDING', (0, 1), (5, -1), 6),    
                ('RIGHTPADDING', (0, 1), (5, -1), 6),   
                ('LEFTPADDING', (6, 1), (6, -1), 8),
                ('RIGHTPADDING', (6, 1), (6, -1), 8),
                ('TOPPADDING', (0, 1), (-1, -1), 6),    
                ('BOTTOMPADDING', (0, 1), (-1, -1), 6), 
                ('ROWSIZE', (0, 1), (-1, -1), 28),
            ]))
            
            story.append(responses_table)
            story.append(Spacer(1, 15))
        
        # Resumen final actualizado
        story.append(Spacer(1, 30))
        story.append(Paragraph("RESUMEN EJECUTIVO", styles['Heading2']))
        
        total_con_comentarios = respuestas.filter(comentarios__isnull=False).exclude(comentarios='').count()
        
        # Encontrar la sección con mejor promedio
        mejor_seccion = ""
        mejor_porcentaje_muy_buena = 0
        for nombre, datos in secciones_stats.items():
            porcentaje_muy_buena = datos['porcentajes'].get('Muy Buena', {}).get('porcentaje', 0)
            if porcentaje_muy_buena > mejor_porcentaje_muy_buena:
                mejor_porcentaje_muy_buena = porcentaje_muy_buena
                mejor_seccion = nombre
        
        resumen_text = f"""
        Este informe contiene un análisis completo de {total_respuestas} respuestas de evaluación 
        recibidas. De estas, {stats['respuestas_completas']} están completas 
        ({(stats['respuestas_completas']/total_respuestas*100):.1f}% de completitud) y 
        {total_con_comentarios} incluyen comentarios adicionales 
        ({(total_con_comentarios/total_respuestas*100):.1f}% con comentarios). 
        El promedio general de calificación es de {stats['promedio_general']:.1f}.
        
        <b>Análisis por secciones:</b> La sección mejor evaluada es {mejor_seccion} con 
        {mejor_porcentaje_muy_buena:.1f}% de calificaciones "Muy Buena". El análisis detallado 
        de porcentajes por cada sección se encuentra en las páginas anteriores.
        
        <b>Todos los comentarios están incluidos en la tabla principal del reporte</b> para facilitar 
        la lectura y análisis conjunto de evaluaciones y observaciones.
        """
        story.append(Paragraph(resumen_text, styles['Normal']))
        
        # Generar PDF
        doc.build(story)
        
        # Preparar respuesta
        pdf_content = buffer.getvalue()
        buffer.close()
        
        response = HttpResponse(pdf_content, content_type='application/pdf')
        filename = f'Informe_Completo_Encuestas_{timezone.now().strftime("%Y%m%d_%H%M")}.pdf'
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response
        
    except ImportError:
        return HttpResponse("""
            <h2>Error: ReportLab no está instalado</h2>
            <p>Para generar PDFs, instala ReportLab:</p>
            <pre>pip install reportlab</pre>
            <p><a href="/dashboard/">Volver al Dashboard</a></p>
        """)
    except Exception as e:
        return HttpResponse(f"""
            <h2>Error generando PDF</h2>
            <p>Error: {str(e)}</p>
            <p><a href="/dashboard/">Volver al Dashboard</a></p>
        """)

# También actualizar la función HTML para mostrar todas las respuestas
@staff_member_required  
def exportar_informe_html(request):
    """Ver informe en HTML para debug - TODAS las respuestas"""
    respuestas = RespuestaEncuesta.objects.all().order_by('-creado_en')
    total_respuestas = respuestas.count()
    
    stats = {
        'total_respuestas': total_respuestas,
        'respuestas_completas': sum(1 for r in respuestas if r.esta_completa()),
        'respuestas_con_comentarios': respuestas.filter(comentarios__isnull=False).exclude(comentarios='').count(),
        'promedio_general': sum(r.calificacion_promedio() for r in respuestas if r.calificacion_promedio() > 0) / total_respuestas if total_respuestas > 0 else 0,
    }
    
    comentarios_destacados = respuestas.filter(comentarios__isnull=False).exclude(comentarios='')[:10]
    
    context = {
        'fecha_generacion': timezone.now(),
        'stats': stats,
        'respuestas_recientes': respuestas,  # TODAS las respuestas, no solo 20
        'comentarios_destacados': comentarios_destacados,
        'es_pdf': False,
    }
    
    return render(request, 'presentaciones/informe.html', context)