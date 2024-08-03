from django.db import models
import base64

class CustomUser(models.Model):
    id = models.AutoField(primary_key=True)
    username = models.CharField(max_length=100)
    userpass = models.CharField(max_length=100)
    created_at = models.DateTimeField()

    class Meta:
        db_table = 'users'
        managed = True  

class Details(models.Model):
    id = models.AutoField(primary_key=True)
    image_name = models.CharField(max_length=255, null=True, blank=True)
    image = models.BinaryField(null=True, blank=True)  # Use BinaryField for blob
    seller_name = models.CharField(max_length=255, null=True, blank=True)
    client_name = models.CharField(max_length=255, null=True, blank=True)
    invoice_number = models.CharField(max_length=255, null=True, blank=True)
    invoice_date = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self):
        return self.invoice_number or 'No Invoice Number'

    def image_base64(self):
        if self.image:
            return base64.b64encode(self.image).decode('utf-8')
        return None

class Items(models.Model):
    invoice = models.ForeignKey(Details, on_delete=models.CASCADE, related_name='items')
    description = models.CharField(max_length=255, null=True, blank=True)
    quantity = models.CharField(max_length=255, null=True, blank=True)
    unit_price = models.CharField(max_length=255, null=True, blank=True)
    net_price = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self):
        return self.description or 'No Description'

class Summary(models.Model):
    invoice = models.OneToOneField(Details, on_delete=models.CASCADE, related_name='summary')
    total = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self):
        return f"Summary for Invoice {self.invoice.invoice_number}"
