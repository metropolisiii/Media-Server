from itertools import chain

from django.forms.widgets import Select, CheckboxSelectMultiple, CheckboxInput, mark_safe
from django.utils.encoding import force_unicode
from django.utils.html import escape, conditional_escape

        
class CheckboxSelectMultipleWithDisabled(CheckboxSelectMultiple):
    """
    Subclass of Django's checkbox select multiple widget that allows disabling checkbox-options.
    To disable an option, pass a dict instead of a string for its label,
    of the form: {'label': 'option label', 'disabled': True}
    """
    def render(self, name, value, attrs=None, choices=()):
        if value is None: value = []
        has_id = attrs and 'id' in attrs
        final_attrs = self.build_attrs(attrs, name=name)
        output = [u'<ul>']
        # Normalize to strings
        str_values = set([force_unicode(v) for v in value])
        for i, (option_value, option_label) in enumerate(chain(self.choices, choices)):
            if final_attrs.has_key('disabled'):
                del final_attrs['disabled']
            if isinstance(option_label, dict):
                if dict.get(option_label, 'disabled'):
                    final_attrs = dict(final_attrs, disabled = 'disabled' )
                option_label = option_label['label']
            # If an ID attribute was given, add a numeric index as a suffix,
            # so that the checkboxes don't all have the same ID attribute.
            if has_id:
                final_attrs = dict(final_attrs, id='%s_%s' % (attrs['id'], i))
                label_for = u' for="%s"' % final_attrs['id']
            else:
                label_for = ''            
            cb = CheckboxInput(final_attrs, check_test=lambda value: value in str_values)
            option_value = force_unicode(option_value)
            rendered_cb = cb.render(name, option_value)
            option_label = conditional_escape(force_unicode(option_label))
            output.append(u'<li><label%s>%s %s</label></li>' % (label_for, rendered_cb, option_label))
        output.append(u'</ul>')
        return mark_safe(u'\n'.join(output))