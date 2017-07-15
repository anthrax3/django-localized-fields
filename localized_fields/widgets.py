from typing import List

from django.conf import settings
from django import forms
from django.contrib.admin import widgets
from django.template.loader import render_to_string

from .value import LocalizedValue


class LocalizedFieldWidget(forms.MultiWidget):
    """Widget that has an input box for every language."""
    template_name = 'localized_fields/multiwidget.html'
    widget = forms.Textarea

    def __init__(self, *args, **kwargs):
        """Initializes a new instance of :see:LocalizedFieldWidget."""

        initial_widgets = [
            self.widget
            for _ in settings.LANGUAGES
        ]

        super().__init__(initial_widgets, *args, **kwargs)

        for ((lang_code, lang_name), widget) in zip(settings.LANGUAGES, self.widgets):
            widget.attrs['lang_code'] = lang_code
            widget.attrs['lang_name'] = lang_name

    def decompress(self, value: LocalizedValue) -> List[str]:
        """Decompresses the specified value so
        it can be spread over the internal widgets.

        Arguments:
            value:
                The :see:LocalizedValue to display in this
                widget.

        Returns:
            All values to display in the inner widgets.
        """

        result = []
        for lang_code, _ in settings.LANGUAGES:
            if value:
                result.append(value.get(lang_code))
            else:
                result.append(None)

        return result


class LocalizedCharFieldWidget(LocalizedFieldWidget):
    """Widget that has an input box for every language."""
    widget = forms.TextInput


class LocalizedFileWidget(LocalizedFieldWidget):
    """Widget that has an file input box for every language."""
    widget = forms.ClearableFileInput


class AdminLocalizedFieldWidget(LocalizedFieldWidget):
    widget = widgets.AdminTextareaWidget
    template = 'localized_fields/admin/widget.html'

    def render(self, name, value, attrs=None):
        if self.is_localized:
            for widget in self.widgets:
                widget.is_localized = self.is_localized

        # value is a list of values, each corresponding to a widget
        # in self.widgets.
        if not isinstance(value, list):
            value = self.decompress(value)

        output = []
        final_attrs = self.build_attrs(attrs)
        id_ = final_attrs.get('id')

        for i, widget in enumerate(self.widgets):
            try:
                widget_value = value[i]
            except IndexError:
                widget_value = None
            if id_:
                final_attrs = dict(final_attrs, id='%s_%s' % (id_, i))

            widget_attrs = self.build_widget_attrs(widget, widget_value, final_attrs)
            output.append(widget.render(name + '_%s' % i, widget_value, widget_attrs))

        context = {
            'id': final_attrs.get('id'),
            'name': name,
            'widgets': zip([code for code, lang in settings.LANGUAGES], output),
            'available_languages': settings.LANGUAGES
        }

        return render_to_string(self.template, context)

    @staticmethod
    def build_widget_attrs(widget, value, attrs):
        attrs = dict(attrs)  # Copy attrs to avoid modifying the argument.

        if (not widget.use_required_attribute(value) or not widget.is_required) \
                and 'required' in attrs:
            del attrs['required']

        return attrs


class AdminLocalizedCharFieldWidget(AdminLocalizedFieldWidget):
    widget = widgets.AdminTextInputWidget


class AdminLocalizedFileFieldWidget(AdminLocalizedFieldWidget):
    widget = widgets.AdminFileWidget
