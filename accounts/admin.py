from django.contrib import admin

# Register your models here.
from .models import CustomUser, Details, Items, Summary


admin.site.register(CustomUser)
admin.site.register(Details)
admin.site.register(Items)
admin.site.register(Summary)

