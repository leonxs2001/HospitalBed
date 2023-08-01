from dashboard.models import DataRepresentation


def initialize():
    __init_data_representation()

def __init_data_representation():
    DataRepresentation.objects.get_or_create(location_type="H", theme_type="I", time_type="T")
    DataRepresentation.objects.get_or_create(location_type="H", theme_type="I", time_type="N")
    DataRepresentation.objects.get_or_create(location_type="H", theme_type="I", time_type="P")

    DataRepresentation.objects.get_or_create(location_type="W", theme_type="I", time_type="T")
    DataRepresentation.objects.get_or_create(location_type="W", theme_type="I", time_type="N")
    DataRepresentation.objects.get_or_create(location_type="W", theme_type="I", time_type="P")

    DataRepresentation.objects.get_or_create(location_type="R", theme_type="I", time_type="T")
    DataRepresentation.objects.get_or_create(location_type="R", theme_type="I", time_type="N")
    DataRepresentation.objects.get_or_create(location_type="R", theme_type="I", time_type="P")

    DataRepresentation.objects.get_or_create(location_type="H", theme_type="W", time_type="T")
    DataRepresentation.objects.get_or_create(location_type="H", theme_type="W", time_type="N")
    DataRepresentation.objects.get_or_create(location_type="H", theme_type="W", time_type="P")

    DataRepresentation.objects.get_or_create(location_type="H", theme_type="R", time_type="T")
    DataRepresentation.objects.get_or_create(location_type="H", theme_type="R", time_type="N")
    DataRepresentation.objects.get_or_create(location_type="H", theme_type="R", time_type="P")

    DataRepresentation.objects.get_or_create(location_type="H", theme_type="B", time_type="T")
    DataRepresentation.objects.get_or_create(location_type="H", theme_type="B", time_type="N")
    DataRepresentation.objects.get_or_create(location_type="H", theme_type="B", time_type="P")

    DataRepresentation.objects.get_or_create(location_type="W", theme_type="R", time_type="T")
    DataRepresentation.objects.get_or_create(location_type="W", theme_type="R", time_type="N")
    DataRepresentation.objects.get_or_create(location_type="W", theme_type="R", time_type="P")

    DataRepresentation.objects.get_or_create(location_type="W", theme_type="B", time_type="T")
    DataRepresentation.objects.get_or_create(location_type="W", theme_type="B", time_type="N")
    DataRepresentation.objects.get_or_create(location_type="W", theme_type="B", time_type="P")

    DataRepresentation.objects.get_or_create(location_type="R", theme_type="B", time_type="T")
    DataRepresentation.objects.get_or_create(location_type="R", theme_type="B", time_type="N")
    DataRepresentation.objects.get_or_create(location_type="R", theme_type="B", time_type="P")

    DataRepresentation.objects.get_or_create(location_type="H", theme_type="H", time_type="P")
    DataRepresentation.objects.get_or_create(location_type="W", theme_type="H", time_type="P")
    DataRepresentation.objects.get_or_create(location_type="R", theme_type="H", time_type="P")