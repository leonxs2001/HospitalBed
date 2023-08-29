from dashboard.models import DataRepresentation


def initialize():
    """Method for initializing all the data of the application."""
    __init_data_representation()

def __init_data_representation():
    """Method for initializing all the DataRepresentations for the application."""
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