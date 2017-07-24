#!/usr/bin/env python
#encoding:utf-8
import os, re
from lxml import etree

class manifestObject(object):
    DEFAULT_NS = 'android'
    def __init__(self, file_path = None):
        self.__file_path = None
        self.__root = None
        self.load(file_path)

    @property
    def file_path(self):
        return self.__file_path

    def load(self, file_path):
        if not (file_path and os.path.exists(file_path)):
            return
        self.__file_path = os.path.abspath(file_path)
        parser = etree.XMLParser(compact=True, remove_blank_text=True)
        self.__root = etree.parse(self.file_path, parser).getroot()

    def __key(self, attribute_name):
        if not attribute_name:
            return None
        pair= None
        if not re.search(r'^%s:'%(manifestObject.DEFAULT_NS), attribute_name):
            pair = [manifestObject.DEFAULT_NS, attribute_name]
        else:
            pair = attribute_name.split(':')
        if not self.__root == None:
            return '{%s}%s'%(self.__root.nsmap.get(pair[0]), pair[1])
        return attribute

    @property
    def __android_ns(self):
        if self.__root == None:
            return ''
        ns_name = manifestObject.DEFAULT_NS
        return 'xmlns:%s="%s"'%(ns_name, self.__root.nsmap.get(ns_name))

    def __xpath(self, xpath):
        if not self.__root == None:
            return self.__root.xpath(xpath, namespaces = self.__root.nsmap)
        return None

    def add(self, xpath, node_name, *attribute_pairs):
        attributes = []
        for item in list(attribute_pairs):
            attributes.append('%s:%s="%s"'%(manifestObject.DEFAULT_NS, item[0], str(item[1])))
        for item in self.__xpath(xpath):
            xml_string = '<%s %s %s/>'%(node_name, self.__android_ns, ' '.join(attributes))
            item.append(etree.XML(xml_string))

    def set_attributes(self, item, *attribute_pairs):
        for pair in list(attribute_pairs):
            key = self.__key(pair[0])
            item.set(key, str(pair[1]))

    def set(self, xpath, attribute_name, value, count = 1):
        num = 0
        for item in self.__xpath(xpath):
            item.set(self.__key(attribute_name), str(value))
            num += 1
            if count > 0 and num >= count:
                break

    def get(self, xpath):
        return self.__xpath(xpath)

    def get_attribute_value(self, element, attribute_name):
        return element.get(self.__key(attribute_name))

    def dump(self, element):
        if isinstance(element, list):
            item_list = []
            for item in element:
                item_list.append(self.__dump(item))
            return '\n'.join(item_list)
        else:
            return self.__dump(element)
    def __dump(self, element):
        if element == None:
            return ''
        return etree.tostring(element, encoding='utf-8', pretty_print=True, with_comments=True)

    def save(self, file_path = None, verbose = False):
        if not file_path:
            file_path = self.file_path
        if not file_path:
            raise Exception('file_path[=%r] invalid'%(file_path))
            return
        file_path = os.path.abspath(file_path)
        if self.__root == None:
            return
        content = self.__dump(self.__root)
        if verbose:
            print content
        with open(file_path, 'w') as fp:
            fp.write(content)
            fp.close()
            print 'SAVE => %s'%(file_path)
