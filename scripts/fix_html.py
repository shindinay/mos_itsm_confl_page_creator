#!/usr/bin/env python3
"""Fix HTML for Confluence using html.parser to properly handle attributes."""

import re
from html.parser import HTMLParser

with open("page_body_8170964_final.html", "r", encoding="utf-8") as f:
    body = f.read()

def cyrillic_to_ascii(s):
    """Convert Cyrillic to ASCII for HTML attributes."""
    replacements = {
        'Шаблонзадачи': 'TaskTemplate',
        'Шаблонзапроса': 'ReqTemplate',
        'ТребованиякРасширениюUI': 'ReqUIExt',
        'Требованиякправиламавтоматизации': 'ReqAutoRule',
        'Общиесведения': 'GeneralInfo',
        'Историяизменений': 'ChangeHistory',
        'Оглавление': 'TableOfContents',
        'Связанныетребования': 'RelatedReqs',
        'Бизнестребования': 'BusinessReqs',
        'ОписаниеПроблемы': 'ProblemDesc',
        'РешениеПроблемы': 'SolutionDesc',
        'Изначальнаяпостановка': 'InitialSpec',
        'Описаниеавтоматизируемогобизнеспроцесса': 'BProcessDesc',
        'Требованиякобъектамсистемы': 'SysObjReqs',
        'ШаблонРабочегопроцесса': 'WfTemplate',
    }
    result = s
    for cyr, a in replacements.items():
        result = result.replace(cyr, a)
    result = ''.join(c if (ord(c) < 128) else '_' for c in result)
    result = re.sub(r'_+', '_', result)
    if result and result[0].isdigit():
        result = 'id_' + result
    return result or 'placeholder'

# Fix: replace all id, name, class, href attributes that contain Cyrillic or unescaped quotes
# Strategy: find all attribute assignments and fix them one by one

def fix_attribute_value(attr_name, value):
    """Fix a single attribute value."""
    # Escape internal double quotes
    if '"' in value:
        value = value.replace('"', '&quot;')
    
    # Convert Cyrillic to ASCII for specific attribute names
    if attr_name.lower() in ('id', 'name', 'class', 'href'):
        if any(ord(c) > 127 for c in value):
            value = cyrillic_to_ascii(value)
    
    return value

# Process the body to fix attributes
# Find all tag starts and extract attributes
def fix_all_tags(html):
    result = []
    i = 0
    while i < len(html):
        if html[i] == '<':
            # Find the end of this tag
            j = html.find('>', i)
            if j == -1:
                result.append(html[i:])
                break
            
            tag_content = html[i+1:j]
            is_closing = tag_content.startswith('/')
            
            if is_closing:
                result.append(html[i:j+1])
                i = j + 1
                continue
            
            # Check if it's a self-closing tag or void element
            void_elements = ['img', 'br', 'hr', 'col', 'colgroup', 'input', 'ri:url', 'ri:user', 'ac:link-body']
            tag_name_match = re.match(r'([a-zA-Z:]+)', tag_content)
            if tag_name_match:
                tag_name = tag_name_match.group(1)
                is_void = tag_name in void_elements
            else:
                tag_name = ''
                is_void = False
            
            # Parse attributes from tag_content
            if is_void and not tag_content.rstrip().endswith('/'):
                result.append('<' + tag_content + '/>')
                i = j + 1
                continue
            
            # Check if it's a self-closing tag
            is_self_closing = tag_content.rstrip().endswith('/')
            
            if not is_closing and not is_void and not is_self_closing:
                result.append('<' + tag_content + '>')
            else:
                result.append('<' + tag_content + '>')
            
            i = j + 1
        else:
            # Find next < or end
            j = html.find('<', i)
            if j == -1:
                # Rest is text - fix & in text content
                text = html[i:]
                # Already escaped in our source, so just pass through
                result.append(text)
                break
            else:
                text = html[i:j]
                result.append(text)
                i = j
    
    return ''.join(result)

# Better approach: use a proper HTML parser
from html.parser import HTMLParser

class Fixer(HTMLParser):
    def __init__(self):
        super().__init__()
        self.output = []
        self.tag_stack = []
    
    def handle_starttag(self, tag, attrs):
        # Fix attributes
        fixed_attrs = []
        for attr_name, attr_value in attrs:
            if attr_value is not None:
                fixed_value = fix_attribute_value(attr_name, attr_value)
            else:
                fixed_value = ''
            if fixed_value:
                fixed_attrs.append((attr_name, '"' + fixed_value + '"'))
        
        # Check if void element or should be self-closing
        void_elements = ['img', 'br', 'hr', 'col', 'colgroup', 'input', 'ri:url', 'ri:user', 'ac:link-body']
        is_void = tag in void_elements
        
        if is_void:
            attr_str = ' '.join(name + '="' + val.strip('"') + '"' for name, val in fixed_attrs)
            if attr_str:
                self.output.append('<' + tag + ' ' + attr_str + ' />')
            else:
                self.output.append('<' + tag + ' />')
        else:
            attr_str = ' '.join(name + '="' + val.strip('"') + '"' for name, val in fixed_attrs)
            if attr_str:
                self.output.append('<' + tag + ' ' + attr_str + '>')
            else:
                self.output.append('<' + tag + '>')
            if tag not in ['style', 'script']:
                self.tag_stack.append(tag)
    
    def handle_endtag(self, tag):
        self.output.append('</' + tag + '>')
        if self.tag_stack and self.tag_stack[-1] == tag:
            self.tag_stack.pop()
    
    def handle_data(self, data):
        self.output.append(data)
    
    def handle_startendtag(self, tag, attrs):
        # Self-closing tag like <br/>
        void_elements = ['img', 'br', 'hr', 'col', 'colgroup', 'input']
        if tag in void_elements:
            attr_str = ' '.join(name + '="' + (val.strip('"') if val else '') + '"' for name, val in attrs if val)
            if attr_str:
                self.output.append('<' + tag + ' ' + attr_str + ' />')
            else:
                self.output.append('<' + tag + ' />')
        else:
            attr_str = ' '.join(name + '="' + (val.strip('"') if val else '') + '"' for name, val in attrs if val)
            if attr_str:
                self.output.append('<' + tag + ' ' + attr_str + '/>')
            else:
                self.output.append('<' + tag + '/>')
    
    def get_output(self):
        return ''.join(self.output)

# Try using html.parser
try:
    fixer = Fixer()
    fixer.feed(body)
    fixed_body = fixer.get_output()
    
    # Clean up
    with open("page_body_8170964_final.html", "w", encoding="utf-8") as f:
        f.write(fixed_body)
    
    print(f"Fixed body: {len(fixed_body)} bytes")
    
    # Verify no more Cyrillic in attributes
    id_cyr = re.findall(r'id="[^"]*[а-яА-ЯёЁ][^"]*"', fixed_body)
    name_cyr = re.findall(r'name="[^"]*[а-яА-ЯёЁ][^"]*"', fixed_body)
    print(f"IDs with Cyrillic: {len(id_cyr)}")
    print(f"Names with Cyrillic: {len(name_cyr)}")
    if id_cyr:
        for ic in id_cyr[:5]:
            print(f"  {ic[:100]}")
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
