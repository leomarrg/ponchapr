from django.core.management.base import BaseCommand
from ponchapr_app.models import Region, LocalOffice

class Command(BaseCommand):
    help = 'Carga las oficinas locales en la base de datos'

    def handle(self, *args, **kwargs):
        # Datos de oficinas por región
        offices_data = [
            # AGUADILLA
            {"rmo": "30201", "region": "AGUADILLA", "office_name": "AGUADA"},
            {"rmo": "30301", "region": "AGUADILLA", "office_name": "AGUADILLA 1"},
            {"rmo": "30302", "region": "AGUADILLA", "office_name": "AGUADILLA 2"},
            {"rmo": "33801", "region": "AGUADILLA", "office_name": "ISABELA"},
            {"rmo": "34401", "region": "AGUADILLA", "office_name": "LAS MARÍAS"},
            {"rmo": "36101", "region": "AGUADILLA", "office_name": "RINCÓN"},
            {"rmo": "35201", "region": "AGUADILLA", "office_name": "MOCA"},
            {"rmo": "37001", "region": "AGUADILLA", "office_name": "SAN SEBASTÍAN"},
            
            # ARECIBO
            {"rmo": "74301", "region": "ARECIBO", "office_name": "LARES"},
            {"rmo": "75301", "region": "ARECIBO", "office_name": "MOROVIS"},
            {"rmo": "71401", "region": "ARECIBO", "office_name": "CAMUY"},
            {"rmo": "72901", "region": "ARECIBO", "office_name": "FLORIDA"},
            {"rmo": "76001", "region": "ARECIBO", "office_name": "QUEBRADILLAS"},
            {"rmo": "77401", "region": "ARECIBO", "office_name": "UTUADO"},
            {"rmo": "72101", "region": "ARECIBO", "office_name": "CIALES"},
            {"rmo": "70901", "region": "ARECIBO", "office_name": "BARCELONETA"},
            {"rmo": "73501", "region": "ARECIBO", "office_name": "HATILLO"},
            {"rmo": "70703", "region": "ARECIBO", "office_name": "ARECIBO 3"},
            {"rmo": "70701", "region": "ARECIBO", "office_name": "ARECIBO 1"},
            {"rmo": "74801", "region": "ARECIBO", "office_name": "MANATI"},
            
            # BAYAMÓN
            {"rmo": "117101", "region": "BAYAMÓN", "office_name": "TOA ALTA"},
            {"rmo": "112701", "region": "BAYAMÓN", "office_name": "DORADO"},
            {"rmo": "112501", "region": "BAYAMÓN", "office_name": "COROZAL"},
            {"rmo": "117601", "region": "BAYAMÓN", "office_name": "VEGA BAJA"},
            {"rmo": "117501", "region": "BAYAMÓN", "office_name": "VEGA ALTA"},
            {"rmo": "117201", "region": "BAYAMÓN", "office_name": "TOA BAJA"},
            {"rmo": "111801", "region": "BAYAMÓN", "office_name": "CATAÑO"},
            {"rmo": "111101", "region": "BAYAMÓN", "office_name": "BAYAMÓN 1"},
            {"rmo": "115501", "region": "BAYAMÓN", "office_name": "NARANJITO"},
            
            # CAGUAS
            {"rmo": "132401", "region": "CAGUAS", "office_name": "COMERIO"},
            {"rmo": "130401", "region": "CAGUAS", "office_name": "AGUAS BUENAS"},
            {"rmo": "131301", "region": "CAGUAS", "office_name": "CAGUAS"},
            {"rmo": "132201", "region": "CAGUAS", "office_name": "CIDRA"},
            {"rmo": "131001", "region": "CAGUAS", "office_name": "BARRANQUITAS"},
            {"rmo": "133401", "region": "CAGUAS", "office_name": "GURABO"},
            {"rmo": "136901", "region": "CAGUAS", "office_name": "SAN LORENZO"},
            
            # CAROLINA
            {"rmo": "167301", "region": "CAROLINA", "office_name": "TRUJILLO ALTO"},
            {"rmo": "166201", "region": "CAROLINA", "office_name": "RIO GRANDE"},
            {"rmo": "164601", "region": "CAROLINA", "office_name": "LOIZA"},
            {"rmo": "161501", "region": "CAROLINA", "office_name": "CANOVANAS"},
            {"rmo": "161601", "region": "CAROLINA", "office_name": "CAROLINA"},
            {"rmo": "164701", "region": "CAROLINA", "office_name": "LUQUILLO"},
            
            # GUAYAMA
            {"rmo": "316801", "region": "GUAYAMA", "office_name": "SANTA ISABEL"},
            {"rmo": "315701", "region": "GUAYAMA", "office_name": "PATILLAS"},
            {"rmo": "316501", "region": "GUAYAMA", "office_name": "SALINAS"},
            {"rmo": "313101", "region": "GUAYAMA", "office_name": "GUAYAMA"},
            {"rmo": "311901", "region": "GUAYAMA", "office_name": "CAYEY"},
            {"rmo": "310801", "region": "GUAYAMA", "office_name": "ARROYO"},
            
            # HUMACAO
            {"rmo": "374101", "region": "HUMACAO", "office_name": "JUNCOS"},
            {"rmo": "373701", "region": "HUMACAO", "office_name": "HUMACAO"},
            {"rmo": "374501", "region": "HUMACAO", "office_name": "LAS PIEDRAS"},
            {"rmo": "372601", "region": "HUMACAO", "office_name": "CULEBRA"},
            {"rmo": "375001", "region": "HUMACAO", "office_name": "MAUNABO"},
            {"rmo": "372001", "region": "HUMACAO", "office_name": "CEIBA"},
            {"rmo": "377701", "region": "HUMACAO", "office_name": "VIEQUES"},
            {"rmo": "375401", "region": "HUMACAO", "office_name": "NAGUABO"},
            {"rmo": "377901", "region": "HUMACAO", "office_name": "YABUCOA"},
            {"rmo": "372801", "region": "HUMACAO", "office_name": "FAJARDO"},
            
            # MAYAGÜEZ
            {"rmo": "516601", "region": "MAYAGÜEZ", "office_name": "SAN GERMAN"},
            {"rmo": "514201", "region": "MAYAGÜEZ", "office_name": "LAJAS"},
            {"rmo": "514901", "region": "MAYAGÜEZ", "office_name": "MARICAO"},
            {"rmo": "513601", "region": "MAYAGÜEZ", "office_name": "HORMIGUEROS"},
            {"rmo": "513001", "region": "MAYAGÜEZ", "office_name": "GUANICA"},
            {"rmo": "511201", "region": "MAYAGÜEZ", "office_name": "CABO ROJO"},
            {"rmo": "510601", "region": "MAYAGÜEZ", "office_name": "AÑASCO"},
            {"rmo": "515101", "region": "MAYAGÜEZ", "office_name": "MAYAGÜEZ"},
            {"rmo": "516401", "region": "MAYAGÜEZ", "office_name": "SABANA GRANDE"},
            
            # PONCE
            {"rmo": "597801", "region": "PONCE", "office_name": "VILLALBA"},
            {"rmo": "590101", "region": "PONCE", "office_name": "ADJUNTAS"},
            {"rmo": "595601", "region": "PONCE", "office_name": "OROCOVIS"},
            {"rmo": "590501", "region": "PONCE", "office_name": "AIBONITO"},
            {"rmo": "591701", "region": "PONCE", "office_name": "CASTAÑER"},
            {"rmo": "592301", "region": "PONCE", "office_name": "COAMO"},
            {"rmo": "593201", "region": "PONCE", "office_name": "GUAYANILLA"},
            {"rmo": "593901", "region": "PONCE", "office_name": "JAYUYA"},
            {"rmo": "594001", "region": "PONCE", "office_name": "JUANA DIAZ"},
            {"rmo": "598001", "region": "PONCE", "office_name": "YAUCO"},
            {"rmo": "595901", "region": "PONCE", "office_name": "PONCE 1"},
            {"rmo": "595902", "region": "PONCE", "office_name": "PONCE 2"},
            {"rmo": "595903", "region": "PONCE", "office_name": "PONCE 3"},
            {"rmo": "595801", "region": "PONCE", "office_name": "PEÑUELAS"},
            
            # SAN JUAN
            {"rmo": "676303", "region": "SAN JUAN", "office_name": "RIO PIEDRAS 3"},
            {"rmo": "673301", "region": "SAN JUAN", "office_name": "GUAYNABO 1"},
            {"rmo": "676701", "region": "SAN JUAN", "office_name": "SAN JUAN"},
            {"rmo": "676301", "region": "SAN JUAN", "office_name": "RIO PIEDRAS 1"},
            {"rmo": "676302", "region": "SAN JUAN", "office_name": "RIO PIEDRAS 2"},
            {"rmo": "676304", "region": "SAN JUAN", "office_name": "RIO PIEDRAS 4"},
        ]

        # Asegúrate de que todas las regiones existan
        regions = set(office["region"] for office in offices_data)
        for region_name in regions:
            Region.objects.get_or_create(name=region_name, defaults={"active": True})

        # Crear las oficinas
        offices_created = 0
        for office_data in offices_data:
            region = Region.objects.get(name=office_data["region"])
            office, created = LocalOffice.objects.get_or_create(
                rmo=office_data["rmo"],
                region=region,
                office_name=office_data["office_name"]
            )
            
            if created:
                offices_created += 1
                self.stdout.write(f"Creada oficina: {office.office_name} en {region.name}")

        self.stdout.write(self.style.SUCCESS(f'Se crearon {offices_created} oficinas locales exitosamente'))

# Guardar este script en ponchapr_app/management/commands/load_offices.py
# Ejecutar con: python manage.py load_offices