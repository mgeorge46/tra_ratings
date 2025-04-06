from django import forms
from .models import NotificationTemplate
from django_ckeditor_5.widgets import CKEditor5Widget

class NotificationTemplateForm(forms.ModelForm):
    class Meta:
        model = NotificationTemplate
        fields = ['name', 'type', 'content']
        widgets = {
            'type': forms.Select(choices=[
                ('email', 'Email'),
                ('sms', 'SMS'),
                ('whatsapp', 'WhatsApp'),
            ]),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        current_type = self.data.get('type', '').lower() or (self.instance.type if self.instance else '').lower()
        if current_type in ['email', 'whatsapp']:
            self.fields['content'].widget = CKEditor5Widget()
