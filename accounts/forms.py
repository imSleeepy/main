from django import forms


class UploadImageForm(forms.Form):
    name = forms.CharField(max_length=255)
    image = forms.ImageField(label='Select an image')