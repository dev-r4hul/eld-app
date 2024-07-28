from django.core.management.base import BaseCommand, CommandError
from version1.utils import db_update_trucks, db_update_drivers


class Command(BaseCommand):
    help = "Update the database with specified data: trucks, drivers, or all"

    def add_arguments(self, parser):
        parser.add_argument(
            "option",
            type=str,
            choices=["trucks", "drivers", "all"],
            help="Specify the data to update: trucks, drivers, or all",
        )

    def handle(self, *args, **kwargs):
        option = kwargs["option"]

        try:
            if option == "trucks":
                self.stdout.write("Updating trucks data...")
                if db_update_trucks():
                    self.stdout.write(self.style.SUCCESS("Successfully updated trucks"))
                else:
                    self.stdout.write(self.style.ERROR("Something went wrong"))

            elif option == "drivers":
                self.stdout.write("Updating drivers data...")
                if db_update_drivers():
                    self.stdout.write(
                        self.style.SUCCESS("Successfully updated drivers")
                    )
                else:
                    self.stdout.write(self.style.ERROR("Something went wrong"))
            elif option == "all":
                self.stdout.write("Updating drivers and trucks data...")
                if db_update_trucks() and db_update_drivers():
                    self.stdout.write(
                        self.style.SUCCESS("Successfully updated drivers and trucks")
                    )
                else:
                    self.stdout.write(self.style.ERROR("Something went wrong"))
            else:
                raise CommandError(
                    "Invalid option. Choose from 'trucks', 'drivers', or 'all'."
                )

        except CommandError as e:
            self.stdout.write(self.style.ERROR(f"Error: {str(e)}"))
