#Foteini Karetsi, A.M. 2990, username: cse52990
#Eleftheria Bella, A.M. 3039, username: cse53039

import sys #needed to exit
import string
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

def displayError(msg): #Prints error message and terminates compiler
    print('Error at line '+str(fline)+ '\n' +msg)
    sys.exit()

#-----Intermediate code functions-----#
#ATTENTION AT str and integer total_quads, temp_value!!!#
quad_program_list = dict() #program's quadruples, dictionary where key=label, value=list of quadruple's operators
total_quads = 0
temp_value = 0
programName = ""

def next_quad(): #returns the number of the next quadruple that will be produced 
    return str(total_quads)

def gen_quad(op=None, x='_', y='_', z='_'):
    global total_quads
    #label = str(total_quads) #considers label as same key, so it only updates the list :(
    quad_program_list[total_quads] = [op, x, y, z] #key is an integer, later maybe should be used as string
    print(quad_program_list[total_quads])
    total_quads +=1
        
def newTemp():
    global temp_value
    tempvar = 'T_'+str(temp_value)
    temp_value +=1
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
        if label in qlist:
            quad_program_list[label][3] = zlabel
    

#-----Lexical Analyzer-----# 
def lex():
    global tokenID, token, fline, f, buffer, counter, state, endOfFile
    #initial values every time lex() begins
    counter = 0 
    state = 0
    my_pos = 0
    buffer = list() #clear buffer
    while(state!=100):
        my_pos = f.tell() #save current position, needed later when have to return back
        ch = f.read(1)
        #print('Buf', f.tell(), 'Ch', ch)
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
    #print(token)    

#-----Definition of Starlet's grammar rules-----#   
def program():
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
                displayError('Error1: Expecting binded word "endprogram", instead of '+ tokenID+'\nTerminating program')
        else:
            displayError('Error2: Expecting program\'s identifier, instead of "'+ tokenID+'"\nTerminating program')
    else:
        displayError('Error3: Expecting binded word "program", instead of "'+ tokenID+'"\nTerminating program')

def block(name):
    declarations()
    subprograms()
    gen_quad('begin_block',name)
    statements()
    if(name == programName):
        gen_quad('halt')
    gen_quad('end_block',name)

def declarations():
    while(tokenID=='declare'):
        lex()
        varlist()
        if(tokenID == ';'):
            lex()
        else:
            displayError('Error4: Expecting ";", or "'+ tokenID+'" is not acceptable.\nTerminating program')

def varlist():
    if(tokenID == IDTK):
        lex()
        while(tokenID == ','):
            lex()
            if(tokenID == IDTK):
                lex()
            else:
                displayError('Error5: Expecting identifier after comma. Terminating program')

def subprograms():
    while(tokenID=='function'):
        subprogram()

def subprogram():
    lex()
    if(tokenID==IDTK):
        funcName = token
        lex()
        funcbody(funcName)
        if(tokenID == 'endfunction'):
            lex()
        else:
            displayError('Error6: Expecting binded word "endfunction". \nTerminating program')
    else:
        displayError('Error7: Expecting function\'s identifier, instead of '+ tokenID+'\nTerminating program')

def funcbody(name):
    formalpars()
    block(name)

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
        lex()
        if(tokenID == IDTK):
            lex()
        else:
            displayError('Error10: Expecting variable\'s identifier after in, or there is a non accepted identifier. Terminating program')
    elif(tokenID == 'inout'):
        lex()
        if(tokenID == IDTK):
            lex()
        else:
            displayError('Error11: Expecting variable\'s identifier after inout, or there is a non accepted identifier. Terminating program')
    elif(tokenID == 'inandout'):
        lex()
        if(tokenID == IDTK):
            lex()
        else:
            displayError('Error12: Expecting variable\'s identifier after inandout, or there is a non accepted identifier. Terminating program')
    else:
        displayError('Error13: Expecting parameter\'s type, instead of '+ tokenID+'.\nTerminating program')

def statements():
    statement()
    while(tokenID == ';'):
        lex()
        statement()

def statement(): #look forward to predict next function
    if(tokenID == IDTK): #assignment-statement, begin with variable
        assignment_stat()
    if(tokenID == 'if'):
        if_stat()
    if(tokenID == 'while'):
        while_stat()
    if(tokenID == 'dowhile'):
        do_while_stat()
    if(tokenID == 'loop'):
        loop_stat()
    if(tokenID == 'exit'):
        exit_stat()
    if(tokenID == 'forcase'):
        forcase_stat()
    if(tokenID == 'incase'):
        incase_stat()
    if(tokenID == 'return'):
        return_stat()
    if(tokenID == 'input'):
        input_stat()
    if(tokenID == 'print'):
        print_stat()

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
        [cond_true,cond_false] = condition()
        if(tokenID == ')'):
            lex()
            if(tokenID == 'then'):
                lex()
                backpatch(cond_true , next_quad())
                statements()
                ifList = make_list(next_quad)
                gen_quad("jump" , "_" , "_" , "_")
                backpatch(cond_false , next_quad())
                elsepart()
                backpatch(ifList , next_quad())
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
    if(tokenID == '('):
        lex()
        condition()
        if(tokenID == ')'):
            lex()
            statements()
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
            [cond_true = cond_false] = condition()
            if(tokenID == ')'):
                lex()
            else:
                displayError('Error8: Expecting ")", instead of '+ tokenID+'.\nTerminating program')
        else:
            backpatch(cond_false , do_while_quad)
            backpatch(cond_true , next_quad())
            displayError('Error9: Expecting "(", instead of '+ tokenID+'.\nTerminating program')
    else:
        displayError('Error18: Expecting binded word "enddowhile", instead of '+ tokenID+'.\nTerminating program')
    
def loop_stat():
    lex()
    statements()
    if(tokenID == 'endloop'):
        lex()
    else:
        displayError('Error19: Expecting binded word "endloop", instead of '+ tokenID+'.\nTerminating program')

def exit_stat():
    lex()

def forcase_stat():
    lex()
    forCaseQuad = next_quad()
    while(tokenID == 'when'):
        lex()
        if(tokenID == '('):
            lex()
            [cond_true , cond_false] = condition()
            backpatch(cond_true , next_quad())
            ##cond_true = makelist(next_quad())
            cond_false = makelist(next_quad())
            if(tokenID == ')'):
                lex()
                if(tokenID == ':'):
                    lex()
                    statements()
                    forCaseList = make_list(next_quad)
                    gen_quad("jump" , "_" , "_" , "_")
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
            gen_quad("jump" , "_" , "_" , "_" , "_")
            if(tokenID == 'enddefault'):
                lex()
                backpatch(forCaseList , next_quad())
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
    lex()
    while(tokenID == 'when'):
        lex()
        if(tokenID == '('):
            lex()
            condition()
            if(tokenID == ')'):
                lex()
                if(tokenID == ':'):
                    lex()
                    statements()
                else:
                    displayError('Error20: Expecting ":", instead of '+ tokenID+'.\nTerminating program')
            else:
                displayError('Error8: Expecting ")", instead of '+ tokenID+'.\nTerminating program')
        else:
            displayError('Error9: Expecting "(", instead of '+ tokenID+'.\nTerminating program')
    if(tokenID == 'endincase'):
        lex()
    else:
        displayError('Error24: Expecting binded word "endincase", instead of '+ tokenID+'.\nTerminating program')

def return_stat(): 
    lex()
    E = expression()
    gen_quad('retv',E)
    
def print_stat(): 
    lex()
    E = expression()
    gen_quad('out',E)

def input_stat(): 
    lex()
    idName = token
    if(tokenID == IDTK):
        lex()
        gen_quad('inp',idName)
    else:
        displayError('Error25: Expecting input identifier, instead of '+ tokenID+'.\nTerminating program')

def actualpars():
    lex()
    actualparlist()
    if(tokenID == ')'):
        lex()
    else:
        displayError('Error8: Expecting ")", instead of '+ tokenID+'.\nTerminating program')
    
def actualparlist():
    if(not(tokenID == ')')):
        actualparitem()
        while(tokenID == ','):
            lex()
            actualparitem()

def actualparitem():
    if(tokenID == 'in'):  
        lex()
        actualparitem_result = expression()
        gen_quad('par', actualparitem_result, 'CV') #create quadruples here when having parameters
    elif(tokenID == 'inout'): 
        lex()
        if(tokenID == IDTK):
            actualparitem_result =token 
            lex()
            gen_quad('par', actualparitem_result, 'REF')
        else:
            displayError('Error11: Expecting variable\'s identifier after inout, or there is a non accepted identifier. Terminating program')
    elif(tokenID == 'inandout'):
        lex()
        if(tokenID == IDTK):
            actualparitem_result = token 
            lex()
            gen_quad('par', actualparitem_result, 'CP')
        else:
            displayError('Error12: Expecting variable\'s identifier after inandout, or there is a non accepted identifier. Terminating program')
    else:
        displayError('Error13: Expecting actual parameter\'s type, instead of '+ tokenID+'.\nTerminating program')

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
        gen_quad('jump')
    return [Rtrue, Rfalse]

def expression():
    optional_sign()
    T1_place = term()
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
        ########## if id without parameters it is a variable, pass it to next level
        factor_result = token
        lex()
        idtail_result = idtail()
        if(idtail_result !=''):
            retValue = newTemp()
            gen_quad('par', retValue, 'RET')
            gen_quad('call', factor_result)
            gen_quad(':=', retValue, '_', factor_result)
    else:
        displayError('Error28: Missing a constant, or a parenthesis or an identifier and nothing matches to what expecting as a factor.\nTerminating program')
    return factor_result

def idtail():
    idtail_result = ''
    if(tokenID == '('):
        actualpars()
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
    if(tokenID == '+' or tokenID=='-'):
        add_oper()


#-----Main function-----#
f = open('test.stl', 'r')
program()
if(not (endOfFile or tokenID=='EOF')):
    print('Syntax error: Cannot recognize characters after "endprogram".')
else:
    print('EOF: Compilation ended successfully!');
f.close()
