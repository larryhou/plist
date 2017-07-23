#!/usr/bin/env python
#encoding:utf-8
import os, re, json

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
            return json.dumps(self.data, sort_keys=True, indent=plistObject.INDENT_SIZE, ensure_ascii=False)
        else:
            return json.dumps(self.data, sort_keys=True, separators=(',',':'), ensure_ascii=False)

    def dump(self):
        result = self.encoding + '\n'
        if self.doctype:
            result += self.doctype + '\n'
        result += '<plist version="%s">\n'%(self.version)
        result += self.__dump(self.data, plistObject.INDENT)
        result += '</plist>'
        return result

    def __dump(self, data, indent = ''):
        object_type = type(data)
        if object_type is dict:
            return self.__dump_dict(data, indent)
        if object_type is list:
            return self.__dump_list(data, indent)
        if object_type is float:
            return '%s<real>%f</real>\n'%(indent, data)
        if object_type is int:
            return '%s<integer>%d</integer>\n'%(indent, data)
        if object_type is str:
            if not data:
                return '%s<string/>\n'%(indent)
            else:
                return '%s<string>%s</string>\n'%(indent, data)
        if object_type is bool:
            return '%s<%s/>\n'%(indent, 'true' if data else 'false')
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
    plist = plistObject(file_path = p.join(p.dirname(p.abspath(__file__)), 'Info_band.plist'))
    print plist.encoding, plist.version
    print plist.doctype
    print plist.file_path
    print plist.json(compact = False)
    print plist.dump()

if __name__ == '__main__':
    main()