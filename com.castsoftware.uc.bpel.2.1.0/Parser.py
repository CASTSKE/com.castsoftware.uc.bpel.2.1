import xml.etree.ElementTree as ET
import re
import hashlib
import cast.analysers.log as CAST
from cast.analysers import Bookmark
class CastOperation():
    
    def __init__(self):
        self.tag_names = []
        self.bpel_file_data = {}
        self.wsdl_file_data = {}
        self.check_sum_with_commented_lines = ""
        self.check_sum_without_commented_lines = "" 
        self.bookmarks = []
        self.stack_line=[]
        self.stack_column=[]
        self.start_line_no = 0
        self.start_column_no =0
        self.end_line_no =0
        self.end_column_no =0
        
    def defineTagNames(self):
        #self.tag_names = ["receive","invoke","process","partnerLink","onMessage","variable","faultHandlers","correlationSet","from","to","onEvent","link"]
        self.tag_names = ["receive","invoke","process","partnerLink","onMessage","variable","faultHandlers","correlationSet","from","to","onEvent","link","assign","catch","catchAll","switch","case","sequence","extension","port","service","operation","if","namespace","binding","portType","reply","copy","input","while"]
    def parseNsmap(self,filename,NS_MAP):
        
        def parseNsXml(root,tag):
            for child in list(root.iter()):
                if tag in re.sub('{.*?}','',str(child.tag)) :
                    return(re.sub('({)|(})|(\')|(\s+)' ,'',str(child.attrib)).split(','))
                
        self.events =["start","start-ns","end-ns"]
        self.root_ns = None
        self.ns_map = []
        for event,elem in ET.iterparse(filename,self.events):
            if "start-ns" in  event:
                self.ns_map.append(elem)
            elif "end-ns" in event:
                self.ns_map.pop()
            elif "start" in event:
                if self.root_ns is None:
                    self.root_ns = elem
                elem.set(NS_MAP,dict(self.ns_map))
                #CAST.debug("NS_MAp"+ "           " + filename + "  " + str(self.ns_map))
        #CAST.debug("Root" + str(self.root_ns) + "&&&&&&&&&&&&&&&&&&&&&&7"  + filename)s
        if filename.endswith('.wsdl'):
            return parseNsXml(ET.ElementTree(self.root_ns),"definitions")
        else:
            #CAST.debug("fine$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$" + str(filename))
            return parseNsXml(ET.ElementTree(self.root_ns),"process")
        
    def getTagAttrib(self,root,tag):
        
        def getNamespace(ele):
            namespace = re.match('\{.*\}',ele.tag)
            return namespace.group(0) if namespace else ''
        
        self.namespace = getNamespace(root)
        self.tag_attrib = []
        match = './/%s'+tag
        for child in root.findall(match % self.namespace):
            self.tag_attrib.append(re.sub('({)|(})|(\')|(\s+)' ,'',str(child.attrib)).split(','))
        return self.tag_attrib
    
    def castParserWsdl(self,filename):
        self.wsdl_file_data["definitions"] = self.parseNsmap(filename,"xmlns:map")
        return self.wsdl_file_data
    
    def castParserBpel(self,file,filename):
        self.defineTagNames()
        self.tree = ET.parse(filename)
        self.root = self.tree.getroot()
        for child_tag in self.tag_names:
            file_data = []
            #file_reference=open(filename,encoding='utf8')
            #file_reference = open(filename,'r')
            #file_data = file_reference.readline()
            file_reference = open(filename,encoding='ISO_8859_1')
#             for i in file_reference:
#                 i.replace("\n","")
#                 file_data.append(i)
            if "process" in child_tag:
                self.bpel_file_data[child_tag]  = self.parseNsmap(filename,"xmlns:map")
                self.bpel_file_data[child_tag+".bookmark"]=self.tagBookmark(file,file_data,child_tag)       
            else:
                self.bpel_file_data[child_tag] = self.getTagAttrib(self.root,child_tag)
                self.bpel_file_data[child_tag+".bookmark"]=self.tagBookmark(file,file_data,child_tag)
        return self.bpel_file_data
    
    def getInvokeJavaCode(self, filename) :
        tree = ET.parse(filename)
        root =tree.getroot()
        invokeJavaCodeList = []
        for child in list(root.iter()) :
            tag = re.sub('{.*?}', '',str(child.tag))
            if tag == "invoke":
                invokeTag = child
            if tag == "javaCode" :
                dict = { invokeTag.attrib["name"] : child.text}
                invokeJavaCodeList.append(dict)
        return invokeJavaCodeList
    
    def tagBookmark(self,file,file_data,tag):
        flag =0
        flag_unclose = 0
        count = 0
        #CAST.debug(tag)
        self.bookmarks=[]
        self.stack_line=[]
        self.stack_column=[]
        for line in file_data:
            count =count+1
            match_reference = re.search('<(.+?):'+tag,line) 
            if not "</" in line and match_reference or "<"+tag in line :
                #CAST.debug(str(match_reference))
                if tag+">" in line:
                    flag_unclose =1
                self.start_line_no = count     
                self.start_column_no =line.find("<")+1
                self.stack_line.append(self.start_line_no)
                self.stack_column.append(self.start_column_no)
                flag = 1
            elif flag == 1:
                self.end_line_no=count
            match_reference_end = re.search('</(.+?):'+tag,line)
            if match_reference_end or "</"+tag in line:
                #CAST.debug(str(count))
                self.end_line_no = count
                self.end_column_no = line.find("</")+1               
                flag = -1
            elif flag_unclose== 1 and "/>" in line:
                self.end_line_no = count
                self.end_column_no = line.find("/>")+1    
                flag_unclose =0        
                flag = -1
            if flag == -1:
                if self.stack_line:
                    self.start_line_no = self.stack_line.pop()
                else:
                    self.start_line_no = self.end_line_no
                if self.stack_column:
                    self.start_column_no = self.stack_column.pop()
                else:
                    self.start_column_no = self.end_column_no
                    
                bookmark = Bookmark(file,self.start_line_no,self.start_column_no,self.end_line_no,self.end_column_no)
                self.bookmarks.append(bookmark)
                #CAST.debug(str(bookmark))
                self.start_line_no = 0
                self.start_column_no =0
                self.end_line_no =0
                self.end_column_no =0
                flag = 0
        return self.bookmarks  
        pass
    
    def fileLoc(self,filename):
        md5_data_with_commented_lines = hashlib.md5()
        md5_data_without_commented_lines = hashlib.md5()
        line_of_code =0
        line_of_comments = 0
        no_of_blank_lines = 0
        flag = 0
        with open(filename,encoding='ISO_8859_1') as source_file:
        #with open(filename,'r') as source_file:
            for line  in source_file:
                if flag == 1:
                    md5_data_with_commented_lines.update(line.encode('ISO_8859_1'))
                    #md5_data_with_commented_lines.update(line.encode('utf-8'))
                    if line.find('-->')==-1:
                        line_of_comments = line_of_comments + 1
                    else:
                        line_of_comments = line_of_comments + 1
                        flag = 0
                else:
                    if len(line) == 1:
                        no_of_blank_lines =no_of_blank_lines + 1
                    elif line.find('<!--')!=-1:
                        md5_data_with_commented_lines.update(line.encode('ISO_8859_1'))
                        #md5_data_with_commented_lines.update(line.encode('utf-8'))
                        
                        line_of_comments = line_of_comments + 1
                        flag = 1
                        if line.find('-->')!=-1 and line.find('-->') > line.find('<!--'):
                            flag =0
                    else:
                        #md5_data_with_commented_lines.update(line.encode('utf-8'))
                        #md5_data_without_commented_lines.update(line.encode('utf-8'))
                        md5_data_with_commented_lines.update(line.encode('ISO_8859_1'))
                        md5_data_without_commented_lines.update(line.encode('ISO_8859_1'))
                        line_of_code = line_of_code +1
        self.check_sum_with_commented_lines = str(md5_data_with_commented_lines.hexdigest())
        self.check_sum_without_commented_lines = str(md5_data_without_commented_lines.hexdigest())  
        return [line_of_comments,line_of_code]
    
    def fileChecksum(self,filename):
        return [self.check_sum_with_commented_lines,self.check_sum_without_commented_lines]
    pass


if __name__ == "__main__":
    '''
    operation = CastOperation()
    print(operation.getInvokeJavaCode("Travel.bpel"))
    '''
    pass