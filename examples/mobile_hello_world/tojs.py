#!/usr/bin/env python2
# Author: Leonardo Cecchi <leonardoce@interfree.it>
# 
# This is free and unencumbered software released into the public domain.
# 
# Anyone is free to copy, modify, publish, use, compile, sell, or
# distribute this software, either in source code form or as a compiled
# binary, for any purpose, commercial or non-commercial, and by any
# means.
# 
# In jurisdictions that recognize copyright laws, the author or authors
# of this software dedicate any and all copyright interest in the
# software to the public domain. We make this dedication for the benefit
# of the public at large and to the detriment of our heirs and
# successors. We intend this dedication to be an overt act of
# relinquishment in perpetuity of all present and future rights to this
# software under copyright law.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
# IN NO EVENT SHALL THE AUTHORS BE LIABLE FOR ANY CLAIM, DAMAGES OR
# OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,
# ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
# OTHER DEALINGS IN THE SOFTWARE.
# 
# For more information, please refer to <http://unlicense.org/>

import xml.etree.ElementTree as ET
import sys
import os
import json

TOJS_VERSION = "1.0"

def toJsString(s):
    """
    This function converts a string to the Javascript literal syntax
    """

    # [MTAB-366]
    # If we have unicode entities in this attribute value we must replace
    # the corresponding unicode character with the javascript escape sequence
    result = "\""

    for c in s:
        if c=='\"':
            result += "\\\""
        elif ord(c)>=32 and ord(c)<=126:
            result += c
        else:
            result += "\\u"+("%0.4X" % ord(c))

    result += "\""
    return result

def tagIsHidden(tagName):
    """
    Check if an tag isn't special for the generator
    """
    if tagName=="Script": return True
    elif tagName=="Constructor": return True
    elif tagName=="Destructor": return True
    elif tagName=="Properties": return True
    elif tagName=="Declarations": return True
    else: return False

def attributeIsHidden(attName):
    """
    Check if an attribute doesn't represent a property
    """
    if attName=="addMethod": return True
    elif attName=="addContext": return True
    elif attName=="id": return True
    elif attName=="layoutParams": return True
    elif attName=="enclosedIn": return True
    elif attName=="constructorArgs": return True
    elif isEventHandlerDeclaration(attName): return True
    else: return False

def toSetterName(s):
    """
    This function get the setter name from
    the property name
    """
    return "set" + s[0].upper() + s[1:]

def toAttributeValue(s):
    if s[0:3]=="tr:":
        return "this.tr(%s)" % toJsString(s[3:])
    elif s[0:4]=="trc:":
        v = s[4:].split("|")
        return "this.trc(%s, %s)" % (toJsString(v[0]), toJsString(v[1]))
    elif s[0:5]=="json:":
        return s[5:]        
    elif s[0:3]=="js:":
        return s[3:]        
    else:
        return toJsString(s)

def isEventHandlerDeclaration(attName):
    """
    Check if an XML attribute represents a event 
    declaration
    """
    return attName[0:2]=="on" and attName[2].isupper()

class Generator(object):
    def __init__(self, config):
        self.__lastChildId = 0
        self.__eventHandlers = []
        self.__config = config

    def __gensym(self):
        self.__lastChildId+=1
        return "__child%i" % self.__lastChildId

    def __wr(self, line):
	# Here I always use the windows CRLF sequence. This is really
	# useful for out VCS mental health
        if "\r" not in line:
            line = line.replace("\n", "\r\n")
        self.ostream.write(line + "\r\n")

    def __emitEventHandlers(self, varName, elem):
        """
        This function emits all the code that add event handlers
        declared in the XML file
        """
        for name in elem.attrib:
            if isEventHandlerDeclaration(name):
                eventName = name[2].lower() + name[3:]
                eventMethod = elem.attrib[name]
                if eventMethod not in self.__eventHandlers: 
                    self.__eventHandlers.append(eventMethod)
                
                self.__wr("      %s.addListener(%s, this.%s, this);" %
                    (varName, toJsString(eventName), eventMethod))

    def __emitAttributes(self, varName, elem):
        """
        This function emits all the code that set properties on
        components
        """
        for name in elem.attrib:
            if not attributeIsHidden(name):
                self.__wr("      %s.%s(%s);" % (varName, toSetterName(name), toAttributeValue(elem.attrib[name])) )

    def __emitAdd(self, parent, childElem, childVar):
        """
        This function emits all the code for adding the child
        component to the parent
        """
        child = childElem.tag

        addContext = parent
        addMethod = "add"
        
        if addContext=="": addContext="this"

        if "addContext" in childElem.attrib:
            addContext = childElem.attrib["addContext"]

        if "addMethod" in childElem.attrib:
            addMethod = childElem.attrib["addMethod"]

        if addContext.startswith("this.this"):
            addContext = addContext[5:]

        if "layoutParams" in childElem.attrib:
            addParameters = ", " + childElem.attrib["layoutParams"]
        else:
            addParameters = ""

        if "enclosedIn" in childElem.attrib:
            beforeEnclosure = childElem.attrib["enclosedIn"] + "("
            afterEnclosure = ")"
        else:
            beforeEnclosure = ""
            afterEnclosure = ""

        self.__wr("      %s.%s(%sthis.%s%s%s);" % (addContext, addMethod, beforeEnclosure, childVar, afterEnclosure, addParameters))

    def __emitChildren(self, varName, elem):
        """
        This function emits the code that creates the children
        of a component
        """
        for child in elem:
            if not tagIsHidden(child.tag):
                if child.tag=="Select":
                    envname = child.attrib["name"].strip()
                    envval = child.attrib["values"].strip()
                    if "getter" in child.attrib:
                        envgetter = child.attrib["getter"].strip()
                    else:
                        envgetter = "qx.core.Environment.get"
                        
                    expr = "qx.lang.Array.contains(%s, %s(%s))" % (envval, envgetter, toJsString(envname))

                    self.__wr("      if(%s) {" % expr)
                    self.__emitChildren(varName, child)
                    self.__wr("      }")

                elif child.tag=="GroupHeader":
                    self.__wr("      this.%s.addGroupHeader(%s);" % (varName,toAttributeValue(child.text)) )

                else:
                    childVar = self.__gensym()
                    if "constructorArgs" in child.attrib:
                        constructorArgs = child.attrib["constructorArgs"]
                    else:
                        constructorArgs = ""

                    self.__wr("      this.%s = new %s(%s);" % (childVar, self.__config.tagToClassName(child.tag), constructorArgs))
                    if "id" in child.attrib:
                        self.__wr("      this.%s = this.%s;" % (child.attrib["id"], childVar))

                    self.__emitAttributes("this."+childVar, child)
                    self.__emitEventHandlers("this."+childVar, child)
                    self.__wr("")
                    self.__emitChildren(childVar, child)
                    self.__emitAdd("this."+varName, child, childVar)


    def reset(self):
        """
        Reset the generator at the initial
        state. Only the configuration is
        retained
        """
        self.__lastChildId = 0
        self.__eventHandlers = []

    def getScript(self, elem):
        s = elem.findtext("./Script")
        if s==None: s = ""
        return s
        
    def getConstructor(self, elem):
        s = elem.findtext("./Constructor")
        if s==None: s = ""
        return s
        
    def getDestructor(self, elem):
        s = elem.findtext("./Destructor")
        if s==None: s = ""
        return s

    def getProperties(self, elem):
        s = elem.findtext("./Properties")
        if s==None: s = ""
        return s

    def getDeclarations(self, elem):
        s = elem.findtext("./Declarations")
        if s==None: s = ""
        return s

    def startMixin(self, inputFile, outputFile, className):
        """
        This function starts the generation of a mixin reading from
        "inputFile" and writing to "outputFile" the class
        with name "className"
        """
        
        self.reset()
        
        elem = ET.parse(open(inputFile, "rb")).getroot()
        self.ostream = open(outputFile, "wb")

        self.__wr("/* Code generated by ToJs v. %s */" % TOJS_VERSION)
        self.__wr("qx.Mixin.define(%s, {" % toJsString(className) )
        self.__wr("")
        self.__wr("  members: {")
        self.__wr("    _createComponents: function() {")
        self.__wr("")

        self.__emitAttributes("this", elem)
        self.__emitEventHandlers("this", elem)
        self.__wr("")

        self.__emitChildren("this", elem)
        
        if len(self.__eventHandlers)>0: sep = ","
        else: sep = ""
        self.__wr("    }")
        self.__wr("  },")

        self.__wr("")
        self.__wr("  destruct: function() {")
        for i in range(self.__lastChildId):
            self.__wr("    this._disposeObjects([%s]);" % toJsString("__child"+str(i+1)) )
            
        self.__wr("  }")
        self.__wr("});")
        
        self.ostream.close()

    def startClass(self, inputFile, outputFile, className):
        """
        This function starts the generation of a class reading from
        "inputFile" and writing to "outputFile" the class
        with name "className"
        """
        
        self.reset()
        
        elem = ET.parse(open(inputFile, "rb")).getroot()
        self.ostream = open(outputFile, "wb")

        self.__wr("/* Code generated by ToJs v. %s */" % TOJS_VERSION)
        self.__wr("qx.Class.define(%s, {" % toJsString(className) )
        self.__wr("")
        self.__wr("  extend : %s," % self.__config.tagToClassName(elem.tag))
        self.__wr("")

        decl = self.getDeclarations(elem)
        if len(decl.strip())>0:
            self.__wr(decl)
            self.__wr(",")
        
        constr = self.getConstructor(elem)
        if len(constr.strip())>0:
            self.__wr("  construct : function()")
            self.__wr("  {")
            self.__wr("    this.base(arguments);")
            self.__wr(constr)
            self.__wr("  },")

        prop = self.getProperties(elem)
        if len(prop.strip())>0:
            self.__wr("  properties : ")
            self.__wr("  {")
            self.__wr(prop.strip())
            self.__wr("  },")

        self.__wr("  members: {")
        self.__wr("    _createComponents: function() {")
        self.__wr("")

        self.__emitAttributes("this", elem)
        self.__emitEventHandlers("this", elem)
        self.__wr("")

        self.__emitChildren("this", elem)
        
        if len(self.__eventHandlers)>0: sep = ","
        else: sep = ""
        self.__wr("    }")
        
        script = self.getScript(elem).strip()
        if len(script)>0:
            self.__wr("    ,")
            for row in script.split("\n"):
                if not row.strip().endswith("//#no"):
                    self.__wr(row)

        self.__wr("  },")
        self.__wr("")
        self.__wr("  destruct: function() {")
        for i in range(self.__lastChildId):
            self.__wr("    this._disposeObjects([%s]);" % toJsString("__child"+str(i+1)) )

        destr = self.getDestructor(elem)
        if len(destr.strip())>0:
            self.__wr(destr)
            
        self.__wr("  }")
        self.__wr("});")
        
        self.ostream.close()
        
class GeneratorConfig(object):
    """
    This class contains the configuration variables
    for the generator
    """
    
    def __init__(self):
        self.__aliases = {} 
        self.__defaultPkg = ""

    def readFile(self, fileName):
        """
        Read the configuration from the specified file
        """
        f = open(fileName, "rb")
        conf = json.load(f)
        f.close()
        
        self.__defaultPkg = conf["defaultPackage"].encode('ascii','ignore')
        
        for name in conf["aliases"]:
            self.__aliases[name]=conf["aliases"][name].encode('ascii','ignore')

    def tagToClassName(self, name):
        """
        Converts, according to the configuration, a tag
        name to a class name
        """
        if "." in name:
            # Name contains the package
            return name
        elif name not in self.__aliases:
            return self.__defaultPkg + "." + name
        else:
            return self.__aliases[name]

def sourceContainsMixIn(fileName):    
    """
    Check the root tag of the source file to see if 
    the file contains a mixin or a class
    """
    try:
        elem = ET.parse(fileName).getroot()
    except Exception as e:
        print "Errore durante il parsing di ", fileName
        sys.exit(1)
    return elem.tag=="tojs"

def sourceContainsClass(fileName):    
    """
    Check the root tag of the source file to see if 
    the file contains a mixin or a class
    """
    try:
        elem = ET.parse(fileName).getroot()
    except Exception as e:
        print "Errore durante il parsing di ", fileName
        sys.exit(1)
    return elem.tag!="tojs"
    
def getTargetClassName(classdir, prefix, sourceFileName):
    className = sourceFileName[len(classdir)+1:-4].replace("\\", ".").replace("/", ".")
                
    # prepend the gen prefix between the
    # project namespace and the class name
    classNameSplit = className.split(".")
    className = classNameSplit[0]+".gen."+".".join(classNameSplit[1:-1]) + "." + prefix + classNameSplit[-1]
    className = className.replace("..", ".")
    
    return className

def getTargetFileName(classdir, className):
    return os.path.normpath(os.path.join(classdir, "./" + className.replace(".","/") + ".js"))
    
def generateMixIn(g, classdir, sourceFileName):
    className = getTargetClassName(classdir, "M", sourceFileName)
    destFileName = getTargetFileName(classdir, className)
    
    if not os.path.exists(os.path.dirname(destFileName)):
        os.makedirs(os.path.dirname(destFileName))
    
    print "  - Mixin",className
    g.startMixin(sourceFileName, destFileName, className)

def generateClass(g, classdir, sourceFileName):
    className = getTargetClassName(classdir, "", sourceFileName)
    destFileName = getTargetFileName(classdir, className)
    
    if not os.path.exists(os.path.dirname(destFileName)):
        os.makedirs(os.path.dirname(destFileName))
    
    print "  - Class",className
    g.startClass(sourceFileName, destFileName, className)
    
def main():
    if len(sys.argv)<2:
        print "Use: %s <applicationDir>" % sys.argv[0]
        return

    rootdir = os.path.normpath(sys.argv[1])
    configFile = os.path.join(rootdir, "tojs_config.json")
    
    if not os.path.exists(configFile):
        raise Exception("Can't find config file at %s" % configFile)

    print "----------------------------------------------------------------------------"
    print "    Mixin generation"
    print "----------------------------------------------------------------------------"
    print
    print ">>> Reading configuration"
    print "  -",configFile
    print
    print ">>> Generate code"

    conf = GeneratorConfig()
    conf.readFile(configFile)    
    configMTime = os.path.getmtime(configFile)

    g = Generator(conf)
    classdir = os.path.normpath(os.path.join(rootdir, "source/class"))
        
    for (dirname, subdirs, files) in os.walk(classdir):
        for f in files:
            if f.lower().endswith(".xml"):
                sourceFileName = os.path.normpath(os.path.join(dirname, f))

                if sourceContainsMixIn(sourceFileName):
                    className = getTargetClassName(classdir, "M", sourceFileName)
                elif sourceContainsClass(sourceFileName):
                    className = getTargetClassName(classdir, "", sourceFileName)
                else:
                    print "ERROR: Wrong base tag", sourceFileName

                destFileName = getTargetFileName(classdir, className)
                
                # Here we need to rigenerate only the necessary classes
                # to enable the Qooxdoo checker to read only the
                # modified classes
                sourceMTime = os.path.getmtime(sourceFileName)
                if os.path.exists(destFileName):
                    destMTime = os.path.getmtime(destFileName)
                    mustCompile = destMTime < sourceMTime or destMTime < configMTime
                else :
                    mustCompile = True

                if mustCompile:
                    if sourceContainsMixIn(sourceFileName):
                        generateMixIn(g, classdir, sourceFileName)
                    elif sourceContainsClass(sourceFileName):
                        generateClass(g, classdir, sourceFileName)
                    else:
                        print "ERROR: Wrong base tag", sourceFileName
    
if __name__=="__main__": main()
