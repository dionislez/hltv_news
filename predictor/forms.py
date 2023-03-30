from django import forms
from datetime import datetime

class DateForm(forms.Form):
    date = forms.DateField(widget=forms.SelectDateWidget(
        years=[i for i in range(2005, datetime.utcnow().year + 1)])
    )