#Foteini Karetsi, A.M. 2990, username: cse52990
#Eleftheria Bella, A.M. 3039, username: cse53039

import sys #needed to exit and read from command line
import string

#-----Different states of Lex()-----# 
#state0 - start
#state1 - id
#state2 - constant
#state3 - /
#state4 - one line comment
#state5 - /* ... */
#state6,11 - nested comments
#state7 - end of multiple comments
#state8 - less than
#state9 - greater than
#state10 - semicolon
#state100 - final states


#-----Syntax analysis-----#
#define global variables
token = '' #string returned by lex
tokenID = '' #id returned by lex
fline = 1 #initialize file line
state = 0 #initialize state
buffer = [] #where token is stored temporarily
counter = 0 #max id size = 30

#-----List of characters used in Starlet programs-----#
whiteletters = list(string.whitespace)
letters = list(string.ascii_letters)
digits = list(string.digits)
usedChars = whiteletters+letters+digits+['+','-','*','/','','=','>','<','(',')','[',']',',',';',':']
#define constants
binded_words = ['program', 'endprogram', 'declare', 'if', 'then', 'else', 'endif', 'while', 'endwhile', 'dowhile', 'enddowhile', 'loop', 'endloop', 'exit', 'forcase', 'endforcase',
                'incase', 'endincase', 'when', 'default', 'enddefault', 'function', 'endfunction', 'return', 'in', 'inout', 'inandout', 'and', 'or', 'not', 'input', 'print']
#extras
IDTK = 'id' #tokenID for identifiers
endOfFile = False #True when reached EOF

#-----Intermediate code global variables-----#
quad_program_list = dict() #program's quadruples, dictionary where key=label, value=list of quadruple's operators
total_quads = 0
temp_value = 0
programName = ""
exitloop = [] #keeps pointer to the quadruple of every exit command, any time you end a loop statement pop last item and backpatch it with the next quad
loopCounterList = []
findLoop = [] #stores first quadruple of every loop statement, return to this quad every time loop starts all over again
checkIfExit = [] #every loop statement sets a temp variable to 0 and if we find an exit statement, this variable becomes 1, when ending statements of loop check if
                 #the corresponding temp variable has changed and if not start from the beginning
allFunctions = [] #stores all function names found in program - use this to avoid using them as variables' names in C file
bindedCharacters = ['CV', 'CP', 'REF', 'RET', '_']

#-----Symbol Array global variables-----#
symbolList = [] #stores scopes of program
mainFramelength = 0
enableReturnSearch = False #detects return statements outside functions

#-----Final Code global variables-----#
mainStartQuad = 0
paramCounter = 0  #count number of parameters when saving values to callee function
cpCallPos = list() #stores the number of the inandout parameter when a function is called, e.g. if x(a,b,c,d) and d=inandout --> cpCallPos = [3]
cpVarNames = list()#stores the corresponding parameter's name

#Display errors and terminate
def displayError(msg): #Prints error message and terminates compiler
    print('Error at line '+str(fline)+ '\n' +msg)
    sys.exit()

#-----Definition of Symbol Array's classes-----#
class Entity:

    def __init__(self, name, entity_type):
        self.name = name
        self.entity_type = entity_type

    def printEntity(self):
        return "Name: " + self.name + ", Type: " + self.entity_type
    
class Variable(Entity):

    def __init__(self, name, entity_type, offset):
        super().__init__(name, entity_type)
        self.offset = offset

    def printEntity(self):
        return "{" + super().printEntity() + ", Offset: " + str(self.offset) + "}"

class Function(Entity):
    
    def __init__(self, name, entity_type):
        super().__init__(name, entity_type)
        self.returnType = "int"
        self.startQuad = -1
        self.argList = []
        self.framelength = 12

    def printEntity(self):
        res = "{" + super().printEntity() + ", Return Type: " + self.returnType + ", StartQuad: " + str(self.startQuad) + ", "
        for arg in self.argList:
            res = res + arg.printArgument() + ", "
        res = res + "Framelength: " + str(self.framelength) + "}"
        return res

class Parameter(Entity):
    
    def __init__(self, name, entity_type, offset, parMode):
        super().__init__(name, entity_type)
        self.offset = offset
        self.parMode = parMode
        
    def printEntity(self):
        return "{" + super().printEntity() + ", Offset: " + str(self.offset) + ", parMode: " + self.parMode + "}"

class Scope:

    def __init__(self, nestingLevel):
        self.nestingLevel = nestingLevel
        self.framelength = 12
        self.scopelist = []

    def printScope(self):
        res = "Nesting level: " + str(self.nestingLevel) 
        for i in self.scopelist:
            res = res +  ", " + i.printEntity()
        res = res  + ", Framelength: " + str(self.framelength)
        return res

class Argument:

    def __init__(self, argMode):
        self.argMode = argMode

    def printArgument(self):
        return "(" + self.argMode + ")"


def printSymbolList():
    print("#-----Symbol Table-----#")
    for i in symbolList:
        print(i.printScope())
        print("\n")

def createArgument(mode, arglist):
    a = Argument(mode)
    arglist.append(a)
    return a

def createVariable(name, entity_type, offset, scopelist):
    v = Variable(name, entity_type, offset)
    scopelist.append(v)

def createFunction(name, entity_type, scopelist):
    f = Function(name, entity_type)
    scopelist.append(f)

def createParameter(name, entity_type, offset, parMode, scopelist):
    p = Parameter(name, entity_type, offset, parMode)
    scopelist.append(p)

def createScope(nestingLevel):
    s = Scope(nestingLevel)
    if(len(symbolList)==0):
        s.nestingLevel = 0
    else:
        s.nestingLevel = symbolList[-1].nestingLevel + 1
    symbolList.append(s)

def deleteScope():
    del symbolList[-1]

def searchEntity(name):
    for s in range(len(symbolList)-1, -1 ,-1):
        for e in symbolList[s].scopelist:
            if e.name == name:
                return e, symbolList[s].nestingLevel
    displayError("Entity " + name + " is not defined.")

def searchVariableOrParameter(sc): 
    if len(sc.scopelist) != 0: 
        for i in range(len(sc.scopelist)-1, -1, -1):
            if sc.scopelist[i].entity_type == "variable" or sc.scopelist[i].entity_type == "parameter":
                return sc.scopelist[i]
    return None

#-----Final code functions-----#
def gnlvcode(v):
    global finalf
    entity, nl = searchEntity(v)
    n = symbolList[-1].nestingLevel - nl - 1
    finalf.write("    lw  $t0, -4($sp)\n")
    for i in range(n):
        finalf.write("    lw  $t0, -4($t0)\n")
    finalf.write("    addi  $t0, $t0, -" + str(entity.offset) + "\n")

def loadvr(v, r):
    global finalf
    currentnl = symbolList[-1].nestingLevel
    entity = None
    nl = -1
    temp = v
    if "-" in v: #negative numbers
        v = v[1:]
    if not v.isdigit():
        entity, nl = searchEntity(v)
    if v.isdigit():
        if temp != v:
            finalf.write("    li  $t" + r + ", " + temp + "\n")
        else:
            finalf.write("    li  $t" + r + ", " + v + "\n")
    elif nl == 0: #nl=0 equals to main function --> global variable
        finalf.write("    lw  $t" + r + ", -" + str(entity.offset) + "($s0)\n")
    elif nl == currentnl and (entity.entity_type == "variable"
                              or (entity.entity_type == "parameter" and (entity.parMode == "in" or entity.parMode == "inandout"))): #local var, temp var and formal par passed by value or by value-restore
        finalf.write("    lw  $t" + r + ", -" + str(entity.offset) + "($sp)\n")
    elif nl == currentnl and (entity.entity_type == "parameter" and entity.parMode == "inout") : #formal par passed by reference
        finalf.write("    lw  $t0, -" + str(entity.offset) + "($sp)\n")
        finalf.write("    lw  $t" + r + ", ($t0)\n")
    elif nl < currentnl and (entity.entity_type == "variable"
                              or (entity.entity_type == "parameter" and (entity.parMode == "in" or entity.parMode == "inandout"))): #local var or formal par passed by value or by value-restore and nl < currentnl
        gnlvcode(v)
        finalf.write("    lw  $t" + r + ", ($t0)\n")
    elif nl < currentnl and (entity.entity_type == "parameter" and entity.parMode == "inout"): #formal par passed by reference and nl < currentnl
        gnlvcode(v)
        finalf.write("    lw  $t0, ($t0)\n")
        finalf.write("    lw  $t" + r + ", ($t0)\n")
    else:
        displayError("Something went wrong at loading value to the register.")

def storerv(r, v):
    global finalf
    currentnl = symbolList[-1].nestingLevel
    entity, nl = searchEntity(v)
    if nl == 0: #global var
        finalf.write("    sw  $t" + r + ", -" + str(entity.offset) + "($s0)\n")
    elif nl == currentnl and (entity.entity_type == "variable"
                              or (entity.entity_type == "parameter" and (entity.parMode == "in" or entity.parMode == "inandout"))): #local var, temp var and formal par passed by value or value/restore
        finalf.write("    sw  $t" + r + ", -" + str(entity.offset) + "($sp)\n")
    elif nl == currentnl and entity.entity_type == "parameter" and entity.parMode == "inout": #formal par passed by reference
        finalf.write("    lw  $t0, -" + str(entity.offset) + "($sp)\n")
        finalf.write("    sw  $t" + r + ",($t0)\n")
    elif nl < currentnl and (entity.entity_type == "variable"
                              or (entity.entity_type == "parameter" and (entity.parMode == "in" or entity.parMode == "inandout"))): #local var or formal par passed by value or by value-restore and nl < currentnl
        gnlvcode(v)
        finalf.write("    sw  $t" + r + ",($t0)\n")
    elif nl < currentnl and entity.entity_type == "parameter" and entity.parMode == "inout": #formal par passed by reference and nl < currentnl
        gnlvcode(v)
        finalf.write("    lw  $t0, ($t0)\n")
        finalf.write("    sw  $t" + r + ",($t0)\n")
    else:
        displayError("Something went wrong at storing value.")

def producemipsfile(quadlist, sq, funcname):
    global finalf, paramCounter, cpCallPos, cpVarNames
    if quadlist[0] == "begin_block" and quadlist[1] != programName:
        finalf.write("L" + str(sq) + ":\n    sw  $ra, ($sp)\n")
    elif quadlist[0] == "begin_block" and quadlist[1] == programName:
        finalf.write("Lmain:\n\n")
        finalf.write("    add  $sp, $sp, " + str(mainFramelength) + "\n")
        finalf.write("    move  $s0, $sp\n")
        #doesn't need to save $ra
    #elif quadlist[0] == "end_block" and quadlist[1] != programName:
        #finalf.write("L" + str(sq) + ":\n    lw  $ra, ($sp)\n")
        #finalf.write("    jr  $ra\n")
    #elif quadlist[0] == "end_block" and quadlist[1] == programName:
    #assignments
    elif quadlist[0] == ":=":
        finalf.write("L" + str(sq) + ":\n")
        loadvr(quadlist[1], "1")
        storerv("1", quadlist[3])
    #operators
    elif quadlist[0] == "+":
        finalf.write("L" + str(sq) + ":\n")
        loadvr(quadlist[1], "1")
        loadvr(quadlist[2], "2")
        finalf.write("    add  $t1, $t1, $t2\n")
        storerv("1", quadlist[3])
    elif quadlist[0] == "-":
        finalf.write("L" + str(sq) + ":\n")
        loadvr(quadlist[1], "1")
        loadvr(quadlist[2], "2")
        finalf.write("    sub  $t1, $t1, $t2\n")
        storerv("1", quadlist[3])
    elif quadlist[0] == "*":
        finalf.write("L" + str(sq) + ":\n")
        loadvr(quadlist[1], "1")
        loadvr(quadlist[2], "2")
        finalf.write("    mul  $t1, $t1, $t2\n")
        storerv("1", quadlist[3])
    elif quadlist[0] == "/":
        finalf.write("L" + str(sq) + ":\n")
        loadvr(quadlist[1], "1")
        loadvr(quadlist[2], "2")
        finalf.write("    div  $t1, $t1, $t2\n")
        storerv("1", quadlist[3])
    #comparisons
    elif quadlist[0] == "<=":
        finalf.write("L" + str(sq) + ":\n")
        loadvr(quadlist[1], "1")
        loadvr(quadlist[2], "2")
        finalf.write("    ble  $t1, $t2, L" + quadlist[3] + "\n")
    elif quadlist[0] == ">=":
        finalf.write("L" + str(sq) + ":\n")
        loadvr(quadlist[1], "1")
        loadvr(quadlist[2], "2")
        finalf.write("    bge  $t1, $t2, L" + quadlist[3] + "\n")
    elif quadlist[0] == "=":
        finalf.write("L" + str(sq) + ":\n")
        loadvr(quadlist[1], "1")
        loadvr(quadlist[2], "2")
        finalf.write("    beq  $t1, $t2, L" + quadlist[3] + "\n")
    elif quadlist[0] == "<":
        finalf.write("L" + str(sq) + ":\n")
        loadvr(quadlist[1], "1")
        loadvr(quadlist[2], "2")
        finalf.write("    blt  $t1, $t2, L" + quadlist[3] + "\n")
    elif quadlist[0] == ">":
        finalf.write("L" + str(sq) + ":\n")
        loadvr(quadlist[1], "1")
        loadvr(quadlist[2], "2")
        finalf.write("    bgt  $t1, $t2, L" + quadlist[3] + "\n")
    elif quadlist[0] == "<>":
        finalf.write("L" + str(sq) + ":\n")
        loadvr(quadlist[1], "1")
        loadvr(quadlist[2], "2")
        finalf.write("    bne  $t1, $t2, L" + quadlist[3] + "\n")
    #jump
    elif quadlist[0] == "jump":
        finalf.write("L" + str(sq) + ":\n")
        finalf.write("    j  " + "L" + quadlist[3] + "\n")
    #return
    elif quadlist[0] == "retv":
        finalf.write("L" + str(sq) + ":\n")
        loadvr(quadlist[1], "1")
        finalf.write("    lw  $t0, -8($sp)\n")
        finalf.write("    sw  $t1, ($t0)\n")
        finalf.write("    lw  $ra, ($sp)\n")
        finalf.write("    jr  $ra\n")
    #input
    elif quadlist[0] == "inp":
        finalf.write("L" + str(sq) + ":\n")
        finalf.write("    li  $v0, 5\n")
        finalf.write("    syscall\n")
        finalf.write("    move $t0, $v0\n")
        storerv("0", quadlist[1])
    #print
    elif quadlist[0] == "out":
        finalf.write("L" + str(sq) + ":\n")
        finalf.write("    li  $v0, 1\n")
        if quadlist[1].isdigit() or ("-" in quadlist[1] and quadlist[1][1:].isdigit()):
            finalf.write("    li  $a0, " + quadlist[1] + "\n")
        else:
            loadvr(quadlist[1], "0")
            finalf.write("    move  $a0, $t0\n")
        finalf.write("    syscall\n")
    #halt
    elif quadlist[0] == "halt":
        finalf.write("L" + str(sq) + ":\n")
        '''finalf.write("    addiu  $v0, $zero, 10\n")
        finalf.write("    syscall\n") '''
    #parameters
    elif quadlist[0] == "par":
        numofCPs = 0
        callee = None
        calleenl = -1
        finalf.write("L" + str(sq) + ":\n")
        if paramCounter == 0:
            #look for the function name in order to get the right framelength afterwards
            enabled = False
            functionName = ""
            for q in quad_program_list:
                if q == sq and quad_program_list[q] == quadlist:
                    enabled = True
                if enabled == True and quad_program_list[q][0] == "call":
                    functionName = quad_program_list[q][1]
                    break
            callee, calleenl = searchEntity(functionName)#search for callee's entity
            finalf.write("    add  $fp, $sp, " + str(callee.framelength) + "\n")
        if quadlist[2] == "CV":
            loadvr(quadlist[1], "0")
            finalf.write("    sw  $t0, -" + str(12 + 4*paramCounter) + "($fp)\n")
        elif quadlist[2] == "REF":
            refParameterActions(quadlist[1])
        elif quadlist[2] == "CP":
            cpCallPos.append(paramCounter)
            cpVarNames.append(quadlist[1])
            loadvr(quadlist[1], "0")
            finalf.write("    sw  $t0, -" + str(12 + 4*paramCounter) + "($fp)\n")
        elif quadlist[2] == "RET":
            f, nl = searchEntity(quadlist[1]) #search temp variable entity and use its offset
            finalf.write("    add  $t0, $sp, -" + str(f.offset) + "\n")
            finalf.write("    sw  $t0, -8($fp)\n")
        paramCounter += 1
    #function call
    elif quadlist[0] == "call":
        f, nl = searchEntity(quadlist[1]) #entity and nesting level of callee function
        if(funcname != programName):
            caller_f, caller_nl = searchEntity(funcname) #returns caller function's entity and in which nesting level (scope) it is stored
        else:
            caller_nl = -1 #main program here
        #if nl = caller_nl, they are declared in the same scope, which means, they are brothers and share the same father
        #if nl > caller_nl, callee is a child of caller
        finalf.write("L" + str(sq) + ":\n")
        if paramCounter == 0:
            finalf.write("    add  $fp, $sp, " + str(f.framelength) + "\n") #when having no actual parameters
        if nl == caller_nl:
            finalf.write("    lw  $t0, -4($sp)\n")
            finalf.write("    sw  $t0, -4($fp)\n")
        elif nl > caller_nl:
            finalf.write("    sw  $sp, -4($fp)\n")
        finalf.write("    add  $sp, $sp, " + str(f.framelength) + "\n")
        finalf.write("    jal L" + str(f.startQuad) + "\n")
        for i in range(len(cpCallPos)):
            var, varnl = searchEntity(cpVarNames[i])
            finalf.write("    lw  $t0, -" + str(12 + 4*cpCallPos[i]) + "($sp)\n")
            finalf.write("    add  $sp, $sp, -" + str(f.framelength) + "\n")
            storerv("0", cpVarNames[i])
            finalf.write("    add  $sp, $sp, " + str(f.framelength) + "\n")
        cpVarNames.clear()
        cpCallPos.clear()
        finalf.write("    add  $sp, $sp, -" + str(f.framelength) + "\n")
        paramCounter = 0 #set to zero for next function execution in the same block        

def refParameterActions(varname):
    global finalf, paramCounter
    var, varnl = searchEntity(varname)
    currentnl = symbolList[-1].nestingLevel
    if varnl == currentnl and var.entity_type == "variable" or (var.entity_type == "parameter" and (var.parMode == "in"
                                                                                                    or var.parMode == "inandout")):
        finalf.write("    add  $t0, $sp, -" + str(var.offset) + "\n")
        finalf.write("    sw  $t0, -" + str(12 + 4*paramCounter) + "($fp)\n")
    elif varnl == currentnl and var.entity_type == "parameter" and var.parMode == "inout":
        finalf.write("    lw  $t0, -" + str(var.offset) + "($sp)\n")
        finalf.write("    sw  $t0, -" + str(12 + 4*paramCounter) + "($fp)\n")
    elif varnl < currentnl and var.entity_type == "variable" or (var.entity_type == "parameter" and (var.parMode == "in"
                                                                                                    or var.parMode == "inandout")):
        gnlvcode(varname)
        finalf.write("    sw  $t0, -" + str(12 + 4*paramCounter) + "($fp)\n")
    elif varnl < currentnl and var.entity_type == "parameter" and var.parMode == "inout":
        gnlvcode(varname)
        finalf.write("    lw $t0, ($t0)\n")
        finalf.write("    sw $t0, -" + str(12 + 4*paramCounter) + "($fp)\n")

#-----Intermediate code functions-----#
def next_quad(): #returns the number of the next quadruple that will be produced 
    return str(total_quads)

def gen_quad(op=None, x="_", y="_", z="_"):
    global total_quads
    quad_program_list[total_quads] = [op, x, y, z]
    total_quads +=1
        
def newTemp():
    global temp_value
    tempvar = 'T_'+str(temp_value)
    temp_value += 1
    offset = symbolList[-1].framelength
    createVariable(tempvar, "variable", offset, symbolList[-1].scopelist)
    symbolList[-1].framelength = symbolList[-1].scopelist[-1].offset + 4
    return tempvar

def emptylist():
    return list()

def makelist(label):
    nl = list()
    nl.append(label)
    return nl

def merge(list1, list2):
    return list1 + list2
    
def backpatch(qlist, zlabel):
    global quad_program_list
    for label in quad_program_list:
        if str(label) in qlist:
            quad_program_list[label][3] = zlabel
    
#-----Lexical Analyzer-----# 
def lex():
    global tokenID, token, fline, f, buffer, counter, state, endOfFile, a
    #initial values every time lex() begins
    counter = 0 
    state = 0
    my_pos = 0
    buffer = list() #clear buffer
    while(state!=100):
        my_pos = f.tell() #save current position, needed later when have to return back
        ch = f.read(1)
        buffer.append(ch)
        if(state==0 and ch in whiteletters):
            del buffer[len(buffer)-1] #ignore whitespaces
            if(ch=='\n'):
                fline+=1
        elif(state==0 and ch in letters): #going to recognize an identifier
            state = 1
            counter +=1
        elif(state==0 and ch in digits): #going to recognize a constant
            state = 2
        elif(state==0 and (ch=='+' or ch=='-' or ch=='*' or ch==',' or ch==';')):
            token = ''.join(buffer)
            tokenID = ch
            state = 100
        elif(state==0 and (ch=='=' or ch=='(' or ch==')' or ch=='[' or ch==']')):
            token = ''.join(buffer)
            tokenID = ch
            state = 100
        elif(state==0 and ch=='<'):
            state = 8
        elif(state==0 and ch=='>'):
            state = 9
        elif(state==0 and ch==':'):
            state = 10
        elif(state==0 and ch==''):
            token = ''.join(buffer)
            tokenID = 'EOF'
            state = 100
        elif(state==0 and ch=='/'):
            state = 3
        elif(state==0 and ch not in usedChars): #character not included in Starlet's vocabulary
            displayError('Not accepted character. Exiting compile')
        elif(state==1 and (ch in letters or ch in digits)):
            state = 1
            counter +=1
        elif(state==1 and not(ch in letters or ch in digits)):
            state = 100
            del buffer[len(buffer)-1]
            if(counter>30):
                token = ''.join(buffer[:30])
            else:
                token = ''.join(buffer)
            if(token in binded_words): #recognize binded words
                tokenID = token
            else:
                tokenID = 'id'
            if(ch==''): #when reading endprogram
                endOfFile = True
                state = 100
            else:
                f.seek(my_pos) #go back one position
        elif(state==2 and ch in letters):
            displayError('Cannot accept identifier\'s name starting with a digit. Terminating program')
        elif(state==2 and not((ch in letters or ch in digits))):
            del buffer[len(buffer)-1]
            token = ''.join(buffer)
            if(int(token)>32767): #constant in range [-32767,32767]
                displayError('Absolute value of constants cannot exceed value 32767. Terminating program')
            else:
                tokenID = 'constant'
                state = 100
                f.seek(my_pos)
        elif(state==3 and ch=='/'):
            state=4 
        elif(state==3 and ch=='*'):
            state=5
        elif(state==3 and ch!='/' and ch!='*'): #recognize division operator
            del buffer[len(buffer)-1]
            token = ''.join(buffer)
            tokenID = '/'
            state = 100
            f.seek(my_pos)
        elif(state==4 and ch=='\n'):
            fline +=1
            state=0
            buffer.clear()
        elif(state==4 and ch==''):
            displayError('File ended without ending comments. Terminating program.')
        elif(state==4 and ch=='/'):
            state=11   
        elif(state==5 and ch=='/'):
            state=6
        elif(state==5 and ch=='\n'):
             fline +=1
        elif(state==5 and ch=='*'):
            state=7
        elif(state==5 and ch==''):
            displayError('File ended without closing comments. Terminating program.')
        elif(state==6 and ch=='*'):
            displayError('Cannot accept nested comments. Terminating program.')
        elif(state==6 and ch=='/'):
            displayError('Cannot accept nested comments (multiple lines, single line comment). Terminating program.')
        elif(state==6 and ch==''):
            displayError('File ended without closing comments. Terminating program.')
        elif(state==6 and ch!='*' and ch!='/' and ch!=''):
            state=5
        elif(state==7 and ch=='/'): #close multiple comment
            state=0
            buffer.clear()
        elif(state==7 and ch!='/'):
            state=5
            if(ch=='\n'):
                fline +=1
        elif(state==8 and ch=='>'):
            state = 100
            token = ''.join(buffer)
            tokenID = '<>'
        elif(state==8 and ch=='='):
            state = 100
            token = ''.join(buffer)
            tokenID = '<='
        elif(state==8 and ch!='>' and ch!='='):
            state = 100
            del buffer[len(buffer)-1]
            token = ''.join(buffer)
            tokenID = '<'
            f.seek(my_pos)
        elif(state==9 and ch=='='):
            state = 100
            token = ''.join(buffer)
            tokenID = '>='
        elif(state==9 and ch!='='):
            state = 100
            del buffer[len(buffer)-1]
            token = ''.join(buffer)
            tokenID = '>'
            f.seek(my_pos)
        elif(state==10 and ch=='='):
            state = 100
            token = ''.join(buffer)
            tokenID = ':='
        elif(state==10 and ch!='='):
            state = 100
            del buffer[len(buffer)-1]
            token = ''.join(buffer)
            tokenID = ':'
            f.seek(my_pos)
        elif(state==11 and ch=='*'):
            displayError('Cannot accept nested comments (single line-multiple line comments). Terminating program.')
        elif(state==11 and ch=='/'):
            displayError('Cannot accept nested single line comments. Terminating program.')
        elif(state==11 and ch==''):
            displayError('File ended without ending comments. Terminating program.')
        elif(state==11 and ch=='\n'):
            fline +=1
            state=0
        elif(state==11 and ch!='*' and ch!='/' and ch!=''):
            state=4    

#-----Definition of Starlet's grammar rules-----#   
def program():
    createScope(0)
    lex() #lexical analyzer - first rule, need to "fill" token & tokenID
    if(tokenID == 'program'):
        lex()
        if(tokenID == IDTK):
            global programName
            programName = token
            lex()
            block(programName)
            if(tokenID == 'endprogram'):
                lex() #expecting eof, or check for sth else
            else:
                displayError('Error1: Expecting binded word "endprogram", instead of ' + tokenID + '\nTerminating program')
        else:
            displayError('Error2: Expecting program\'s identifier, instead of "' + tokenID + '"\nTerminating program')
    else:
        displayError('Error3: Expecting binded word "program", instead of "' + tokenID + '"\nTerminating program')

def block(name, returnList = []):
    global mainFramelength, enableReturnSearch, mainStartQuad, paramCounter
    paramCounter = 0 #set to zero every time a new block is executed
    f = None
    declarations()
    subprograms()
    if name != programName:
        f, nl = searchEntity(name)
        f.startQuad = next_quad()
    gen_quad("begin_block", name)
    if name == programName:
        enableReturnSearch = True
    statements(returnList)
    if(name == programName):
        gen_quad("halt")
    gen_quad("end_block", name)
    if len(symbolList[-1].scopelist) != 0:
        v = searchVariableOrParameter(symbolList[-1])
        if v != None:
            if name == programName:
                mainFramelength = v.offset + 4
                symbolList[-1].framelength = mainFramelength
            else:
                f.framelength = v.offset + 4 #sets function's framelength when function ends
                symbolList[-1].framelength = f.framelength
    else:
        f.framelength = 12 #sets function's framelength when function ends
        symbolList[-1].framelength = f.framelength
    print("BEFORE ERASURE")
    printSymbolList()
    quadlist = list()
    if(f != None): #case function
        sq = int(f.startQuad)
        while(sq >=0 and quad_program_list[sq][0] != "end_block"):
            producemipsfile(quad_program_list[sq], sq, f.name)
            sq += 1
            quadlist = quad_program_list[sq]
        producemipsfile(quadlist, sq, f.name)
        sq += 1
        mainStartQuad = sq #Main starts when all functions are compiled, this variable is updated every time a new block is compiled 
    else:
        sq = mainStartQuad
        while(quad_program_list[sq][0] != "end_block"):
            producemipsfile(quad_program_list[sq], sq, programName)
            sq += 1
            quadlist = quad_program_list[sq]
        ##main's end_block
        producemipsfile(quadlist, sq, programName)
    deleteScope()
    print("UPDATED ARRAY")
    printSymbolList()

def declarations():
    while(tokenID =='declare'):
        lex()
        varlist()
        scope = symbolList[-1]
        for entity1 in scope.scopelist:
            flag = 0
            for entity2 in scope.scopelist:
                if entity1.name == entity2.name:
                    flag = flag + 1
            if flag > 1:
                displayError('Cannot accept the same name for different variables in the same scope.')
        if(tokenID == ';'):
            lex()
        else:
            displayError('Error4: Expecting ";", or token "'+ tokenID+'" is not acceptable.\nTerminating program')

def varlist():
    if(tokenID == IDTK):
        offset = symbolList[-1].framelength
        createVariable(token, "variable", offset, symbolList[-1].scopelist)
        symbolList[-1].framelength = symbolList[-1].scopelist[-1].offset + 4
        lex()
        while(tokenID == ','):
            lex()
            if(tokenID == IDTK):
                offset = symbolList[-1].framelength
                createVariable(token, "variable", offset, symbolList[-1].scopelist)
                symbolList[-1].framelength = symbolList[-1].scopelist[-1].offset + 4
                lex()
            else:
                displayError('Error5: Expecting identifier after comma not ' + token + '. Terminating program')

def subprograms():
    while(tokenID=='function'):
        subprogram()

def subprogram():
    returnList = []
    lex()
    if(tokenID==IDTK):
        funcName = token
        allFunctions.append(funcName)
        createFunction(funcName, "function", symbolList[-1].scopelist)
        scope = symbolList[-1]
        e = scope.scopelist[-1]
        flag = 0
        for i in range(len(scope.scopelist)-1):
            if scope.scopelist[i].name == e.name:
                    flag = flag + 1
        if flag >= 1:
            displayError('Cannot accept the same name for variables/functions in the same scope.')
        createScope(symbolList[-1].nestingLevel +1)
        lex()
        funcbody(funcName, returnList)
        if len(returnList) == 0:
            displayError('No return statement found in function ' + funcName + '. Terminating program')
        if(tokenID == 'endfunction'):
            lex()
        else:
            displayError('Error6: Expecting binded word "endfunction". \nTerminating program')
    else:
        displayError('Error7: Expecting function\'s identifier, instead of '+ tokenID+'.\nTerminating program')

def funcbody(name, returnList):
    formalpars()
    block(name, returnList)

def formalpars():
    if(tokenID == '('):
        lex()
        formalparlist()
        if(tokenID == ')'):
            lex()
        else:
            displayError('Error8: Expecting ")", instead of '+ tokenID+' or ")" is missing.\nTerminating program')
    else:
        displayError('Error9: Expecting "(", instead of '+ tokenID+' or "(" is missing.\nTerminating program')

def formalparlist():
    if(not(tokenID == ')')):
        formalparitem()
        while(tokenID == ','):
            lex()
            formalparitem()

def formalparitem():
    if(tokenID == 'in'):
        arg = createArgument(token, symbolList[-2].scopelist[-1].argList)
        lex()
        if(tokenID == IDTK):
            offset = symbolList[-1].framelength
            createParameter(token, "parameter", offset, arg.argMode, symbolList[-1].scopelist)
            symbolList[-1].framelength = symbolList[-1].scopelist[-1].offset + 4
            lex()
        else:
            displayError('Error10: Expecting variable\'s identifier after in, or there is a non accepted identifier. Terminating program')
    elif(tokenID == 'inout'):
        arg = createArgument(token, symbolList[-2].scopelist[-1].argList)
        lex()
        if(tokenID == IDTK):
            offset = symbolList[-1].framelength
            createParameter(token, "parameter", offset, arg.argMode, symbolList[-1].scopelist)
            symbolList[-1].framelength = symbolList[-1].scopelist[-1].offset + 4
            lex()
        else:
            displayError('Error11: Expecting variable\'s identifier after inout, or there is a non accepted identifier. Terminating program')
    elif(tokenID == 'inandout'):
        arg = createArgument(token, symbolList[-2].scopelist[-1].argList)
        lex()
        if(tokenID == IDTK):
            offset = symbolList[-1].framelength
            createParameter(token, "parameter", offset, arg.argMode, symbolList[-1].scopelist)
            symbolList[-1].framelength = symbolList[-1].scopelist[-1].offset + 4
            lex()
        else:
            displayError('Error12: Expecting variable\'s identifier after inandout, or there is a non accepted identifier. Terminating program')
    else:
        displayError('Error13: Expecting parameter\'s type, instead of '+ tokenID+'.\nTerminating program')

def statements(returnList = []):
    statement(returnList)
    while(tokenID == ';'):
        lex()
        emptys = statement(returnList)
        if(emptys == 1):
            displayError('Redundant character ; after last executed statement' + '.\nTerminating program.')

def statement(returnList = []): #look forward to predict next function
    #detect empty statement, if 1 and there is ; in the last statement, display error
    empty_stat = 1
    if(tokenID == IDTK): #assignment-statement, begin with variable
        assignment_stat()
        empty_stat = 0
    if(tokenID == 'if'):
        if_stat()
        empty_stat = 0
    if(tokenID == 'while'):
        while_stat()
        empty_stat = 0
    if(tokenID == 'dowhile'):
        do_while_stat()
        empty_stat = 0
    if(tokenID == 'loop'):
        loop_stat()
        empty_stat = 0
    if(tokenID == 'exit'):
        exit_stat()
        empty_stat = 0
    if(tokenID == 'forcase'):
        forcase_stat()
        empty_stat = 0
    if(tokenID == 'incase'):
        incase_stat()
        empty_stat = 0
    if(tokenID == 'return'):
        return_stat(returnList)
        empty_stat = 0
    if(tokenID == 'input'):
        input_stat()
        empty_stat = 0
    if(tokenID == 'print'):
        print_stat()
        empty_stat = 0
    return empty_stat

def assignment_stat():
    idName = token
    lex()
    if(tokenID == ':='):
        lex()
        E = expression()
        gen_quad(":=",E,"_",idName)
    else:
        displayError('Error14: Expecting assignment operator, instead of '+ tokenID+'.\nTerminating program')

def if_stat():
    lex()
    if(tokenID == '('):
        lex()
        [cond_true, cond_false] = condition()
        if(tokenID == ')'):
            lex()
            if(tokenID == 'then'):
                lex()
                backpatch(cond_true, next_quad())
                statements()
                ifList = makelist(next_quad())
                gen_quad("jump")
                backpatch(cond_false, next_quad())
                elsepart()
                backpatch(ifList, next_quad())
                if(tokenID == 'endif'):
                    lex()
                else:
                    displayError('Error15: Expecting binded word "endif", instead of '+ tokenID+'.\nTerminating program')
            else:
                displayError('Error16: Expecting binded word "then", instead of '+ tokenID+'.\nTerminating program')
        else:
            displayError('Error8: Expecting ")", instead of '+ tokenID+'.\nTerminating program')
    else:
        displayError('Error9: Expecting "(", instead of '+ tokenID+'.\nTerminating program')

def elsepart():
    if(tokenID == 'else'):
        lex()
        statements()

def while_stat():
    lex()
    while_quad = next_quad()
    if(tokenID == '('):
        lex()
        [condTrue, condFalse] = condition()
        if(tokenID == ')'):
            lex()
            backpatch(condTrue, next_quad())
            statements()
            gen_quad("jump", "_", "_", while_quad)
            backpatch(condFalse, next_quad())
            if(tokenID == 'endwhile'):
                lex()
            else:
                displayError('Error17: Expecting binded word "endwhile", instead of '+ tokenID+'.\nTerminating program')
        else:
            displayError('Error8: Expecting ")", instead of '+ tokenID+'.\nTerminating program')
    else:
        displayError('Error9: Expecting "(", instead of '+ tokenID+'.\nTerminating program')

def do_while_stat():
    lex()
    do_while_quad = next_quad()
    statements()
    if(tokenID == 'enddowhile'):
        lex()
        if(tokenID == '('):
            lex()
            [cond_true, cond_false] = condition()
            if(tokenID == ')'):
                lex()
                backpatch(cond_false, do_while_quad)
                backpatch(cond_true, next_quad())
            else:
                displayError('Error8: Expecting ")", instead of '+ tokenID+'.\nTerminating program')
        else:
            displayError('Error9: Expecting "(", instead of '+ tokenID+'.\nTerminating program')
    else:
        displayError('Error18: Expecting binded word "enddowhile", instead of '+ tokenID+'.\nTerminating program')
    
def loop_stat():
    loopCounterList.append(next_quad())
    lex()
    t = newTemp()
    checkIfExit.append(t)
    gen_quad(":=", "0", "_", checkIfExit[-1])
    findLoop.append(next_quad())
    statements()
    if(tokenID == 'endloop'):
        lex()
        gen_quad("=", checkIfExit[-1], "0", findLoop[-1])
        exitJump = makelist(exitloop.pop())
        backpatch(exitJump, next_quad())
        checkIfExit.pop()
        findLoop.pop()
        loopCounterList.pop()
    else:
        displayError('Error19: Expecting binded word "endloop", instead of '+ tokenID+'.\nTerminating program')

def exit_stat():
    if not loopCounterList: #if list does not have elements 
        displayError('ALERT: Exit statement(s) used outside loop statements. Terminating program')
    lex()
    gen_quad(":=", "1", "_", checkIfExit[-1])
    exitQuad = next_quad()
    gen_quad("jump")
    exitloop.append(exitQuad)

def forcase_stat():
    lex()
    forcase_quad = next_quad()
    exitList = emptylist()
    while(tokenID == 'when'):
        lex()
        if(tokenID == '('):
            lex()
            [cond_true, cond_false] = condition()
            if(tokenID == ')'):
                lex()
                if(tokenID == ':'):
                    backpatch(cond_true, next_quad())
                    lex()
                    statements()
                    forcaseList = makelist(next_quad())
                    gen_quad("jump")
                    backpatch(cond_false, next_quad())
                    exitList = merge(exitList, forcaseList)
                else:
                    displayError('Error20: Expecting ":", instead of '+ tokenID+'.\nTerminating program')
            else:
                displayError('Error8: Expecting ")", instead of '+ tokenID+'.\nTerminating program')
        else:
            displayError('Error9: Expecting "(", instead of '+ tokenID+'.\nTerminating program')
    if(tokenID == 'default'):
        lex()
        if(tokenID == ':'):
            lex()
            statements()
            gen_quad("jump", "_", "_", forcase_quad)
            backpatch(exitList, next_quad())
            if(tokenID == 'enddefault'):
                lex()
                if(tokenID == 'endforcase'):
                    lex()
                else:
                    displayError('Error21: Expecting binded word "endforcase", instead of '+ tokenID+'.\nTerminating program')
            else:
                displayError('Error22: Expecting binded word "enddefault", instead of '+ tokenID+'.\nTerminating program')       
        else:
           displayError('Error20: Expecting ":", instead of '+ tokenID+'.\nTerminating program')
    else:
        displayError('Error23: Expecting binded word "default", instead of '+ tokenID+'.\nTerminating program')
            
def incase_stat():
    t = newTemp()
    flagQ = next_quad()
    gen_quad(":=", "0", "_", t)
    lex()
    while(tokenID == 'when'):
        lex()
        if(tokenID == '('):
            lex()
            [cond_true, cond_false] = condition()
            if(tokenID == ')'):
                lex()
                if(tokenID == ':'):
                    lex()
                    backpatch(cond_true, next_quad())
                    gen_quad(":=", "1", "_", t)
                    statements()
                    backpatch(cond_false, next_quad())
                else:
                    displayError('Error20: Expecting ":", instead of '+ tokenID+'.\nTerminating program')
            else:
                displayError('Error8: Expecting ")", instead of '+ tokenID+'.\nTerminating program')
        else:
            displayError('Error9: Expecting "(", instead of '+ tokenID+'.\nTerminating program')
    if(tokenID == 'endincase'):
        gen_quad("=", t, "1", flagQ)
        lex()
    else:
        displayError('Error24: Expecting binded word "endincase", instead of '+ tokenID+'.\nTerminating program')

def return_stat(returnList): 
    lex()
    E = expression()
    if enableReturnSearch:
        displayError('Found return statement out of function range. Terminating program')
    returnQuad = next_quad()
    gen_quad("retv", E)
    returnList.append(returnQuad)
    
def print_stat(): 
    lex()
    E = expression()
    gen_quad("out", E)

def input_stat(): 
    lex()
    idName = token
    if(tokenID == IDTK):
        lex()
        gen_quad("inp", idName)
    else:
        displayError('Error25: Expecting input identifier, instead of '+ tokenID+'.\nTerminating program')

def actualpars(argList):
    lex()
    aList = actualparlist()
    if len(argList) < len(aList):
        displayError('Too many arguments assigned for this function.')
    elif len(argList) > len(aList):
        displayError('This function accepts ' + str(len(argList)) + ' arguments. You inserted ' + str(len(aList)))
    if argList != aList :
        displayError('Arguments assigned are different than the ones that the function is defined with.')
    if(tokenID == ')'):
        lex()
    else:
        displayError('Error8: Expecting ")", instead of '+ tokenID+'.\nTerminating program')
    
def actualparlist():
    aList = []
    if(not(tokenID == ')')):
        aType = actualparitem()
        aList.append(aType)
        while(tokenID == ','):
            lex()
            aType = actualparitem()
            aList.append(aType)
    return aList

def actualparitem():
    type_result = ''
    if(tokenID == 'in'):
        type_result = tokenID
        lex()
        actualparitem_result = expression()
        gen_quad("par", actualparitem_result, "CV")
    elif(tokenID == 'inout'):
        type_result = tokenID
        lex()
        if(tokenID == IDTK):
            actualparitem_result = token 
            lex()
            gen_quad("par", actualparitem_result, "REF")
        else:
            displayError('Error11: Expecting variable\'s identifier after inout, or there is a non accepted identifier. Terminating program')
    elif(tokenID == 'inandout'):
        type_result = tokenID
        lex()
        if(tokenID == IDTK):
            actualparitem_result = token 
            lex()
            gen_quad("par", actualparitem_result, "CP")
        else:
            displayError('Error12: Expecting variable\'s identifier after inandout, or there is a non accepted identifier. Terminating program')
    else:
        displayError('Error13: Expecting actual parameter\'s type, instead of '+ tokenID+'.\nTerminating program')
    return type_result

def condition():
    [Q1true, Q1false] = boolterm()
    Btrue = Q1true
    Bfalse = Q1false
    while(tokenID == 'or'):
        backpatch(Bfalse, next_quad())
        lex()
        [Q2true, Q2false] = boolterm()
        Btrue = merge(Btrue, Q2true)
        Bfalse = Q2false
    return [Btrue, Bfalse]

def boolterm():
    [R1true, R1false] = boolfactor()
    Qtrue = R1true
    Qfalse = R1false
    while(tokenID == 'and'):
        backpatch(Qtrue, next_quad())
        lex()
        [R2true, R2false] = boolfactor()
        Qfalse = merge(Qfalse, R2false)
        Qtrue = R2true
    return [Qtrue, Qfalse]

def boolfactor():
    if(tokenID == 'not'):
        lex()
        if(tokenID == '['):
            lex()
            [Btrue, Bfalse] = condition()
            if(tokenID == ']'):
                Rtrue = Bfalse
                Rfalse = Btrue
                lex()
            else:
                displayError('Error26: Expecting "]", instead of '+ tokenID+'.\nTerminating program')
        else:
            displayError('Error27: Expecting "[", instead of '+ tokenID+'.\nTerminating program')
    elif(tokenID == '['):
        lex()
        [Btrue, Bfalse] = condition()
        if(tokenID == ']'):
            Rtrue = Btrue
            Rfalse = Bfalse
            lex()
        else:
            displayError('Error26: Expecting "]", instead of '+ tokenID+'.\nTerminating program')
    else:
        E1 = expression()
        relop = relational_oper()
        E2 = expression()
        Rtrue = makelist(next_quad())
        gen_quad(relop,E1,E2,"_")
        Rfalse = makelist(next_quad())
        gen_quad("jump")
    return [Rtrue, Rfalse]

def expression():
    opt_sign = optional_sign()
    T1_place = term()
    if opt_sign=='-':
        T1_place = opt_sign + T1_place
    while(tokenID == '+' or tokenID == '-'):
        sign = token
        add_oper()
        T2_place = term()
        w = newTemp()
        gen_quad(sign,T1_place,T2_place,w)
        T1_place = w
    return T1_place

def term():
    F1_place = factor()
    while(tokenID == '*' or tokenID == '/'):
        operator = token 
        mul_oper()
        F2_place = factor()
        w = newTemp()
        gen_quad(operator,F1_place,F2_place,w)
        F1_place = w
    return F1_place

def factor():
    factor_result = ''
    if(tokenID == 'constant'):
        factor_result = token
        lex()
    elif(tokenID == '('):
        lex()
        E = expression()
        if(tokenID == ')'):
            factor_result = E
            lex()
        else:
            displayError('Error8: Expecting ")", instead of '+ tokenID+'.\nTerminating program')
    elif(tokenID == IDTK):
        factor_result = token
        lex()
        entity, nl = searchEntity(factor_result)
        parList = []
        if entity.entity_type == 'function':
            parList = []
            for a in entity.argList:
                parList.append(a.argMode)
        idtail_result = idtail(parList)
        if(idtail_result !=''):
            if entity.entity_type != 'function':
                displayError('Trying to use ' + entity.entity_type + ' ' + entity.name + ' as a function.')
            retValue = newTemp()
            gen_quad("par", retValue, "RET")
            gen_quad("call", factor_result)
            factor_result = retValue
        else:
            if entity.entity_type == 'function':
                displayError('Trying to use function as a variable.')
    else:
        displayError('Error28: Missing a constant, or a parenthesis or an identifier and nothing matches to what expecting as a factor.\nTerminating program')
    return factor_result

def idtail(argList):
    idtail_result = ''
    if(tokenID == '('):
        actualpars(argList)
        idtail_result = 'arguments'
    return idtail_result

def relational_oper():
    relop = token
    if(tokenID == '='):
        lex()
    elif(tokenID == '<='):
        lex()
    elif(tokenID == '>='):
        lex()
    elif(tokenID == '>'):
        lex()
    elif(tokenID == '<'):
        lex()
    elif(tokenID == '<>'):
        lex()
    else:
        displayError('Error29: Expecting a relational operator, instead of '+ tokenID+'.\nTerminating program')
    return relop

def add_oper():
    if(tokenID == '+'):
        lex()
    elif(tokenID == '-'):
        lex()
    else:
        displayError('Error30: Expecting an additional operator, instead of '+ tokenID+'.\nTerminating program')
  
def mul_oper():
    if(tokenID == '*'):
        lex()
    elif(tokenID == '/'):
        lex()
    else:
        displayError('Error31: Expecting a multiplier operator, instead of '+ tokenID+'.\nTerminating program')

def optional_sign():
    sign = token
    if(tokenID == '+' or tokenID=='-'):
        add_oper()
    return sign    

def checkIfNegative(variables, s):
    temp_var = ""
    if s[0] == '-':
        temp_var = s[1:]
    if temp_var != "":
        if isinstance(temp_var, str) and not temp_var.isdigit() and temp_var not in variables:
            variables.append(temp_var)
    else:
        if isinstance(s, str) and not s.isdigit() and s not in variables:
            variables.append(s)

def produceCFile(name):
    global programName
    #if some variables are declared in declarations section but not used afterwards, they will not
    #be declared in C code, because they are not useful. However, symbol array contains them normally.
    variables = []
    blockNames = []
    for q in quad_program_list:
        if (quad_program_list[q][0] == "begin_block") or (quad_program_list[q][0] == "end_block"):
            if quad_program_list[q][1] not in blockNames and quad_program_list[q][1] != programName:
                blockNames.append(quad_program_list[q][1])
            continue
        checkIfNegative(variables, quad_program_list[q][1])
        checkIfNegative(variables, quad_program_list[q][2])
        checkIfNegative(variables, quad_program_list[q][3])
    for f in allFunctions:
        if f in variables:
            variables.remove(f)
    for c in bindedCharacters:
        if c in variables:
            variables.remove(c)
    cfile = open(name + '.c', 'w')
    cfile.write("#include <stdio.h>\n\n")
    if quad_program_list[0][0] and (quad_program_list[0][1] != programName):
        #another function is declared not main
        cfile.write('int main(){\n\tprintf("Warning: Functions included, cannot produce correct C file.");\n\treturn 0;\n}\n')
        cfile.close()
        return
    for i in quad_program_list:
        if (quad_program_list[i][0] == "begin_block") and (quad_program_list[i][1] == programName): 
            cfile.write("int main()\n{\n")
            cfile.write("\tint ")
            for var in range(len(variables)-1):
                cfile.write(variables[var] + ", ")
            cfile.write(variables[-1] + ";\n")
        elif quad_program_list[i][0] == ":=" :
            #assign
            cfile.write("\tL_" + str(i) + ":" + "\t" + str(quad_program_list[i][3]) + " = " + str(quad_program_list[i][1]) + ";" + "  // " + str(quad_program_list[i]) + "\n")
        #operators
        elif quad_program_list[i][0] == "+" :
            if quad_program_list[i][3] not in variables:
                variables.append(quad_program_list[i][3])
            cfile.write("\tL_" + str(i) + ":" + "\t" + str(quad_program_list[i][3]) + " = " + str(quad_program_list[i][1]) + " + " + str(quad_program_list[i][2]) + ";" + "  // " + str(quad_program_list[i]) + "\n")
        elif quad_program_list[i][0] == "-" :
            if quad_program_list[i][3] not in variables:
                variables.append(quad_program_list[i][3])
            cfile.write("\tL_" + str(i) + ":" + "\t" + str(quad_program_list[i][3]) + " = " + str(quad_program_list[i][1]) + " - " + str(quad_program_list[i][2]) + ";" + "  // " + str(quad_program_list[i]) + "\n")
        elif quad_program_list[i][0] == "*" :
            if quad_program_list[i][3] not in variables:
                variables.append(quad_program_list[i][3])
            cfile.write("\tL_" + str(i) + ":" + "\t" + str(quad_program_list[i][3]) + " = " + str(quad_program_list[i][1]) + " * " + str(quad_program_list[i][2]) + ";" + "  // " + str(quad_program_list[i]) + "\n")
        elif quad_program_list[i][0] == "/" :
            if quad_program_list[i][3] not in variables:
                variables.append(quad_program_list[i][3])
            cfile.write("\tL_" + str(i) + ":" + "\t" + str(quad_program_list[i][3]) + " = " + str(quad_program_list[i][1]) + " / " + str(quad_program_list[i][2]) + ";" + "  // " + str(quad_program_list[i]) + "\n")
        #comparisons
        elif quad_program_list[i][0] == "<=" :
            cfile.write("\tL_" + str(i) + ":" + "\t" + "if " + "(" + str(quad_program_list[i][1]) + str(quad_program_list[i][0]) + str(quad_program_list[i][2]) + ") " + "goto L_" + str(quad_program_list[i][3]) +";"  + "  // " + str(quad_program_list[i]) + "\n")
        elif quad_program_list[i][0] == ">=" :
            cfile.write("\tL_" + str(i) + ":" + "\t" + "if " + "(" + str(quad_program_list[i][1]) + str(quad_program_list[i][0]) + str(quad_program_list[i][2]) + ") " + "goto L_" + str(quad_program_list[i][3]) +";" + "  // " + str(quad_program_list[i]) + "\n")
        elif quad_program_list[i][0] == "=" :
            cfile.write("\tL_" + str(i) + ":" + "\t" + "if " + "(" + str(quad_program_list[i][1]) + str(quad_program_list[i][0]) + str(quad_program_list[i][0]) + str(quad_program_list[i][2]) + ") " + "goto L_" + str(quad_program_list[i][3]) +";" + "  // " + str(quad_program_list[i]) + "\n")
        elif quad_program_list[i][0] == "<" :
            cfile.write("\tL_" + str(i) + ":" + "\t" + "if " + "(" + str(quad_program_list[i][1]) + str(quad_program_list[i][0]) + str(quad_program_list[i][2]) + ") " + "goto L_" + str(quad_program_list[i][3]) +";" + "  // " + str(quad_program_list[i]) + "\n")
        elif quad_program_list[i][0] == ">" :
            cfile.write("\tL_" + str(i) + ":" + "\t" + "if " + "("  + str(quad_program_list[i][1]) + str(quad_program_list[i][0]) + str(quad_program_list[i][2]) + ") " + "goto L_" + str(quad_program_list[i][3]) +";" + "  // " + str(quad_program_list[i]) + "\n")
        elif quad_program_list[i][0] == "<>" :
            cfile.write("\tL_" + str(i) + ":" + "\t" + "if" + "(" + str(quad_program_list[i][1]) + "!=" + str(quad_program_list[i][2]) + ") " + "goto L_" + str(quad_program_list[i][3]) +";" + "  // " + str(quad_program_list[i]) + "\n")
        #jump
        elif quad_program_list[i][0] == "jump":
            cfile.write("\tL_" + str(i) + ":" + "\t" + "goto L_"+ str(quad_program_list[i][3])+ ";" + "  // " + str(quad_program_list[i]) + "\n")
        #return 
        elif quad_program_list[i][0] ==  "retv" :
            cfile.write("\tL_" + str(i) + ":" + "\t" + "return " + str(quad_program_list[i][1]) + ";" + "  // " + str(quad_program_list[i]) + "\n")
        #input
        #input works as scanf in C
        elif quad_program_list[i][0] == "inp" :
            cfile.write("\tL_" + str(i) + ":" + "\t" + 'scanf("%d", &' + str(quad_program_list[i][1]) + ");" + "  // " + str(quad_program_list[i]) + "\n")
        #output
        #print works as printf in C
        elif quad_program_list[i][0] == "out" :
            result = quad_program_list[i][1].isdigit()
            if result:
                cfile.write("\tL_" + str(i) + ":" + "\t" + 'printf("%d\\n", ' + str(quad_program_list[i][1]) + ");" + "  // " + str(quad_program_list[i]) + "\n")
            else:
                cfile.write("\tL_" + str(i) + ":" + "\t" + 'printf("' + str(quad_program_list[i][1]) + ' = %d\\n", ' + str(quad_program_list[i][1]) + ");" + "  // " + str(quad_program_list[i]) + "\n")
        #exit program
        elif quad_program_list[i][0] == "halt" :
            cfile.write("\tL_" + str(i) + ":" + "\t" + "return 0;"  + " // " + str(quad_program_list[i]) + "\n")
            cfile.write("}")
    cfile.close()

#-----Main function-----#

if(len(sys.argv)<2):
    print("Error: Expecting file name.")
    sys.exit()
tokens = sys.argv[1].split(".") #keep file name without the ending, to create intermediate code file and C file
f = open(sys.argv[1], 'r') #read file name as command line argument
finalf = open(tokens[0] + '.asm', 'w') #assembly file
finalf.write("    j  Lmain\n")
program()
if(not (endOfFile or tokenID=='EOF')):
    print('Syntax error: Cannot recognize characters after "endprogram".')
else:
    print('EOF: Compilation ended successfully!');
with open(tokens[0] + ".int", 'w') as interFile:
    for l in quad_program_list:
        interFile.write(str(l)+' '+str(quad_program_list[l])+' \n')
f.close()
finalf.close()
produceCFile(tokens[0])
