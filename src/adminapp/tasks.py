import datetime

from pathlib import Path
from openpyxl import Workbook
from openpyxl.styles import Font

from django.conf import settings
from celery import shared_task
from celery.utils.log import get_task_logger

from .models import InverterData, ZipReport, Location

logger = get_task_logger(__name__)


@shared_task(bind=True)
def generate_zip(extra_key=None, location_list=None, report_id=None, from_date=None, to_date=None):
    report_instance = ZipReport.objects.filter(pk=report_id).first()
    report_instance.status = "Generating"
    report_instance.save()
    for record in location_list:
        try:
            location = Location.objects.filter(pk=record).first()
            report_instance.location.add(location)
            context = None
            start_data = InverterData.objects.filter(device__location=location,
                                                     created_at__date__gte=from_date,
                                                     is_active=True).first()
            end_data = InverterData.objects.filter(device__location=location,
                                                   created_at__date__lte=to_date,
                                                   is_active=True).last()
            wb = Workbook()
            sheet = wb['Sheet']
            wb.remove(sheet)
            ws1 = wb.create_sheet("Plant Summery")
            ws2 = wb.create_sheet("Plant Analysis")
            # ws3 = wb.create_sheet("Grid Downtime Analysis")
            # ws4 = wb.create_sheet("Inverter Summery ")
            # ws5 = wb.create_sheet("Alarm Analysis")
            # ws6 = wb.create_sheet("Help & Support")
            plant_summery_data = []
            plant_analysis_data = []
            if end_data and start_data:
                context = {
                    "total_energy": int(end_data.total_energy) - int(start_data.total_energy),
                    "daily_energy": int(end_data.daily_energy) - int(start_data.daily_energy),
                    "op_active_power": int(end_data.op_active_power) - int(start_data.op_active_power),
                    "specific_yields": int(end_data.specific_yields) - int(start_data.specific_yields)
                }

                inverter_data = InverterData.objects.filter(device__location=location,
                                                            created_at__date__lte=to_date,
                                                            created_at__date__gte=from_date,
                                                            is_active=True).last()
                pr, cuf, insolation = 0, 0, 0
                irradiation = 250
                insolation = irradiation * 24
                if context and "specific_yields" in context and inverter_data:
                    pr = (int(inverter_data.specific_yields) * 100) / 24
                    cuf = pr / 365 * 24 * 12

                plant_summery_data = [
                    ['Plant Name', location.name],
                    ['Date', from_date,
                     to_date],
                    ['Description'],
                    ['Plant Capacity', "", "kWp"],
                    ['Plant Manager'],
                    ['Manager Phone'],
                    [''],
                    ['Daily Energy', context['daily_energy'] if 'daily_energy' in context else "--", "kWh"],
                    ['Output Active Power', context['op_active_power'] if 'op_active_power' in context else "--",
                     "kWp"],
                    ['Specific Yield', context['specific_yields'] if 'specific_yields' in context else "--", "kWh/kWp"],
                    ['CUF', cuf, "%"],
                    ['Performance Ratio', pr, "%"],
                    ['Total Energy', context['total_energy'] if 'total_energy' in context else "--", "MWh"],
                    ['Solar Insolation', insolation, "KWh/m2"],
                    ['Solar Irradiation', irradiation, "W/m2"],
                ]
                inverter_data = InverterData.objects.filter(device__location=location,
                                                            created_at__date__lte=to_date,
                                                            created_at__date__gte=from_date,
                                                            is_active=True)
                for inverter in inverter_data.iterator():
                    inverter_pr = (int(inverter.specific_yields) * 100) / 24
                    inverter_cuf = int(inverter_pr) / 365 * 24 * 12
                    plant_analysis_data.append(
                        [inverter.created_at.replace(tzinfo=None), inverter.daily_energy, inverter.op_active_power,
                         inverter.specific_yields,
                         inverter_cuf, inverter_pr, inverter.total_energy, insolation, irradiation])
            else:
                plant_summery_data = [
                    ['Plant Name', location.name],
                    ['Date', from_date,
                     to_date],
                    ['Description'],
                    ['Plant Capacity', "", "kWp"],
                    ['Plant Manager'],
                    ['Manager Phone'],
                    ['']]
                plant_analysis_data = [['Error', "No data for the selected range"]]
            for row in plant_summery_data:
                ws1.append(row)
            ws2.append(["Timestamp", "Daily Energy [ kWh ]", "Output Active Power [ kWp ]",
                        "Specific Yield [ kWh/kWp ]", "CUF [ % ]", "Performance Ratio [ % ]",
                        "Total Energy [ MWh ]", "Solar Insolation [ KWh/m2 ]", "Solar Irradiation [ W/m2 ]"])
            red_font = Font(bold=True, italic=True)
            for cell in ws2["1:1"]:
                cell.font = red_font
            for row in plant_analysis_data:
                ws2.append(row)
            Path(settings.MEDIA_ROOT + "/" + str(report_instance.id)).mkdir(parents=True, exist_ok=True)
            wb.save('{}/{}/{}.xlsx'.format(settings.MEDIA_ROOT, str(report_instance.id), location.name))
        except Exception as e:
            print(e)
            report_instance.status = "Error"
            report_instance.save()
            return None
    report_instance.status = "Success"
    report_instance.save()
    return None
