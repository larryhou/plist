#!/usr/bin/env python
#encoding:utf-8
import os, re, json, base64, time
class dataObject(object):
    def __init__(self, base64_string = None):
        self.bytes = None
        self.load(base64_string)
    def load(self, base64_string):
        if base64_string:
            self.bytes = base64.b64decode(base64_string)
            return self.bytes
        return None
    def dump(self, line_size = 64, indent = None):
        if not indent:
            indent = ''
        if self.bytes:
            data = base64.b64encode(self.bytes)
            if line_size <= 0:
                return indent + data
            else:
                result, position = '', 0
                length = len(data)
                while position < length:
                    segement = data[position:position+line_size]
                    result += '%s%s\n'%(indent, segement)
                    num = len(segement)
                    if num < line_size:
                        break
                    position += num
                return result
        else:
            return ''
class dateObject(object):
    FORMAT = '%Y-%m-%dT%H:%M:%SZ'
    def __init__(self, date_string = None):
        self.date = None
        self.load(date_string)
    @property
    def date_string(self):
        if self.date:
            return time.strftime(dateObject.FORMAT, self.date)
        return None
    def load(self, date_string):
        if date_string:
            senconds = time.mktime(time.strptime(date_string, dateObject.FORMAT)) - time.altzone
            self.date = time.localtime(senconds)
            return self.date
        return None
    def dump(self):
        if self.date:
            senconds = time.mktime(self.date) + time.altzone
            return time.strftime(dateObject.FORMAT, time.localtime(senconds))
        else:
            return ''

class jsonEncoder(json.JSONEncoder):
    def default(self, data):
        if isinstance(data, dataObject):
            return data.dump(line_size = 0)
        if isinstance(data, dateObject):
            return data.dump()
        else:
            return json.JSONEncoder.default(self, data)

class plistObject(object):
    INDENT_SIZE = 4
    INDENT = ' ' * INDENT_SIZE
    def __init__(self, file_path = None):
        self.encoding = '<?xml version="1.0" encoding="UTF-8"?>'
        self.version = '1.0'
        self.data, self.__file_path, self.doctype = None, None, None
        self.load(file_path)

    @property
    def file_path(self):
        return self.__file_path

    def json(self, compact = False):
        if not compact:
            return json.dumps(self.data, cls=jsonEncoder, sort_keys=True, indent=plistObject.INDENT_SIZE, ensure_ascii=False)
        else:
            return json.dumps(self.data, cls=jsonEncoder, sort_keys=True, separators=(',',':'), ensure_ascii=False)

    def dump(self):
        result = self.encoding + '\n'
        if self.doctype:
            result += self.doctype + '\n'
        result += '<plist version="%s">\n'%(self.version)
        result += self.__dump(self.data, plistObject.INDENT)
        result += '</plist>'
        return result

    def __dump(self, data, indent = ''):
        data_type = type(data)
        if data_type is dict:
            return self.__dump_dict(data, indent)
        if data_type is list:
            return self.__dump_list(data, indent)
        if data_type is float:
            return '%s<real>%f</real>\n'%(indent, data)
        if data_type is int:
            return '%s<integer>%d</integer>\n'%(indent, data)
        if data_type is str:
            if not data:
                return '%s<string/>\n'%(indent)
            else:
                return '%s<string>%s</string>\n'%(indent, data)
        if data_type is bool:
            return '%s<%s/>\n'%(indent, 'true' if data else 'false')
        if data_type is dataObject:
            return '%s<data>\n%s%s</data>\n'%(indent, data.dump(indent = indent), indent)
        if data_type is dateObject:
            return '%s<date>%s</date>\n'%(indent, data.dump())
    def __dump_list(self, data, indent):
        result = '%s<array>\n'%(indent)
        for value in data:
            result += self.__dump(value, indent + plistObject.INDENT)
        result += '%s</array>\n'%(indent)
        return result
    def __dump_dict(self, data, indent):
        result = '%s<dict>\n'%(indent)
        key_list = data.keys()
        key_list.sort()
        for key in key_list:
            value = data.get(key)
            result += '%s<key>%s</key>\n'%(indent + plistObject.INDENT, key)
            result += self.__dump(value, indent + plistObject.INDENT)
        result += '%s</dict>\n'%(indent)
        return result
    def load(self, file_path):
        if not (file_path and os.path.exists(file_path)):
            return
        self.__file_path = os.path.abspath(file_path)
        self.data = None
        buffer = open(self.__file_path, 'r')
        element, char = None, None
        while char == None or char:
            char = buffer.read(1)
            if char == '<':
                element = ''
            element += char
            if char == '>':
                if element[:5] == '<?xml':
                    self.encoding = element
                elif element[:9] == '<!DOCTYPE':
                    self.doctype = element
                elif element[:6] == '<plist':
                    version_match = re.search(r'version\s*=\s*["\']([^"\']+)', element)
                    if version_match:
                        self.version = version_match.group(1)
                    self.data = self.__parse(buffer)
                    break
                else:
                    print element
                element = ''
        return self.data
    def __parse(self, buffer):
        element, char = '', None
        while char == None or char:
            char = buffer.read(1)
            if not char:
                break
            if char == '<':
                element = ''
            element += char
            if char == '>':
                if element == '<dict>':
                    return self.__parse_dict(buffer)
                if element == '<array>':
                    return self.__parse_list(buffer)
                if element == '<string>':
                    return self.__parse_rest_node(buffer, element)
                if element == '<real>':
                    return float(self.__parse_rest_node(buffer, element).strip())
                if element == '<integer>':
                    return int(self.__parse_rest_node(buffer, element).strip())
                if element == '<date>':
                    return dateObject(self.__parse_rest_node(buffer, element).strip())
                if element == '<data>':
                    return dataObject(self.__parse_rest_node(buffer, element).strip())
                value_match = re.match(r'^<([^/>]+)/>$', element)
                if value_match:
                    value = value_match.group(1).strip()
                    if value == 'string':
                        return ''
                    if value in ('true', 'false'):
                        return value == 'true'
                    return value
                close_match = re.match(r'^</[^>]+>$', element)
                if close_match:
                    return None
                return self.__parse_rest_node(buffer, element)
                element = ''

    def __parse_dict(self, buffer):
        data = {}
        element, char = '', None
        while char == None or char:
            char = buffer.read(1)
            if char == '<':
                element = ''
            element += char
            if char == '>':
                if element == '<key>':
                    key = self.__parse_rest_node(buffer, element)
                    data[key] = self.__parse(buffer)
                else:
                    return data

    def __parse_list(self, buffer):
        data = []
        while True:
            item = self.__parse(buffer)
            if item:
                data.append(item)
            else:
                return data

    def __parse_rest_node(self, buffer, tag):
        tag = tag[:1] + '/' + tag[1:]
        element, char, text = '', None, None
        while char == None or char:
            char = buffer.read(1)
            if char == '<':
                text = element
                element = ''
            element += char
            if char == '>':
                if element != tag:
                    raise Exception('parsing close tag fails')
                return text
        raise Exception('parsing simple value fails')

    def __parse_node(self, buffer):
        is_open = False
        element, char = '', None
        while char == None or char:
            char = buffer.read(1)
            if char == '<':
                element = ''
            element += char
            if char == '>':
                return self.__parse_rest_node(buffer, element)
def main():
    import os.path as p
    plist = plistObject(file_path = p.join(p.dirname(p.abspath(__file__)), 'data.plist'))
    print plist.file_path
    print plist.json(compact = False)
    print plist.dump()

if __name__ == '__main__':
    main()