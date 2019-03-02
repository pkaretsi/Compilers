import sys #needed to exit
import string
#-----Syntax analysis-----#
#define global variables
token = '' #string returned by lex
tokenID = '' #id returned by lex
fline = 1 #initialize file line
state = 0 #initialize state
buffer = []  
whiteletters = list(string.whitespace)
#del whiteletters[2]
letters = list(string.ascii_letters)
digits = list(string.digits)
usedChars = whiteletters+letters+digits+['+','-','*','/','','=','>','<','(',')','[',']',',',';',':']
counter = 0 #max id size = 30
#state0 - start
#state1 - id
#state2 - constant
#state3 - /
#state4 - one line comment
#state5 - /* ... */
#state6,11 - nested comments
#state7 - end of comment
#state8 - less than
#state9 - greater than
#state10 - :
#state-1 - error
#state100 - final states (+eof)
#define constants
binded_words = ['program', 'endprogram', 'declare', 'if', 'then', 'else', 'endif', 'do', 'while', 'endwhile', 'loop', 'endloop', 'exit', 'forcase', 'endforcase',
                'incase', 'endincase', 'when', 'default', 'enddefault', 'function', 'endfunction', 'return', 'in', 'inout', 'inandout', 'and', 'or', 'not', 'input', 'print']
#extras
IDTK = 'id'
indo_while = False
endOfFile = False

def displayError(msg):
    print('Error at line '+str(fline)+ '\n' +msg)
    sys.exit()
 
def lex():
    global tokenID, token, fline, f, buffer, counter, state, endOfFile
    counter = 0
    state = 0
    my_pos = 0
    buffer = list()
    while(state!=100):# and state!=-1):
        print('Entering at pos ',f.tell())
        my_pos = f.tell()
        ch = f.read(1)
        
        print('Buf', f.tell(), 'Ch', ch)
        buffer.append(ch)
        if(state==0 and ch in whiteletters):
            #state = 0
            del buffer[len(buffer)-1] #same in comments
            if(ch=='\n'):
                fline+=1
        elif(state==0 and ch in letters):
            state = 1
            counter +=1
        elif(state==0 and ch in digits):
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
            #print('Xanamphka')
            state = 10
        elif(state==0 and ch==''):
            #if(endOfFile != True):
            token = ''.join(buffer)
            tokenID = 'EOF'
            state = 100 #eof - maybe tokens?
        elif(state==0 and ch=='/'):
            #print('Vrhka diairesh')
            state = 3
        elif(state==0 and ch not in usedChars):
        #elif(state==0 and not(ch in letters)and not(ch in whiteletters) and not(ch in digits) and ch!='+' and ch!='-' and ch!='*' and ch!='/' and ch!=',' and ch!=';'
        #     and ch!='=' and ch!='(' and ch!=')' and ch!='[' and ch!=']' and ch!=':' and ch!='<' and ch!='>' and ch!=''):
            displayError('Not accepted character. Exiting lex')
        elif(state==1 and (ch in letters or ch in digits)):# and counter<30):
            state = 1
            counter +=1
        elif(state==1 and not(ch in letters or ch in digits)):# and counter<30)):
            state = 100
            del buffer[len(buffer)-1]
            print('Last Character', ch)
            print(f.tell())
            #print(buffer)
            if(counter>30):
                token = ''.join(buffer[:30])
            else:
                token = ''.join(buffer)
            print(token)
            if(token in binded_words):
                tokenID = token
            else:
                tokenID = 'id'
            #pos = f.tell() - 1
            #print('Ending id', pos)
            if(ch==''):
                endOfFile = True
                state = 100
            else:
                print('pos before', f.tell())
                f.seek(my_pos)
                print('New pos', f.tell())
            #print('New pos', f.tell())
        #elif(state==2 and ch in digits):
        #    state = 2
        elif(state==2 and ch in letters):
            displayError('Cannot accept identifier\'s name starting with a digit. Terminating program')
        elif(state==2 and not((ch in letters or ch in digits))):
            del buffer[len(buffer)-1]
            token = ''.join(buffer) #maybe int(str(buffer))
            if(int(token)>32767):
                displayError('Absolute value of constants cannot exceed value 32767. Terminating program')
            else:
                tokenID = 'constant'
                state = 100
                f.seek(my_pos)
        elif(state==3 and ch=='/'):
            #print('Mphka')
            state=4
        elif(state==3 and ch=='*'):
            #print(ch)
            #print('Mphkaaaaaa')
            state=5
        elif(state==3 and ch!='/' and ch!='*'):
            #print('Found what ? after /', ch)
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
             #state=5
        elif(state==5 and ch=='*'):
            state=7
        elif(state==5 and ch==''):
            #print('Character":', ch)
            displayError('File ended without closing comments. Terminating program.')
        #elif(state==5 and ch!='/' and ch!='\n' and ch!='*' and ch!=''):
        #    state=5
        elif(state==6 and ch=='*'):
            displayError('Cannot accept nested comments. Terminating program.')
        elif(state==6 and ch=='/'):
            displayError('Cannot accept nested comments (multiple lines, single line comment). Terminating program.')
        elif(state==6 and ch==''):
            displayError('File ended without closing comments. Terminating program.')
        elif(state==6 and ch!='*' and ch!='/' and ch!=''):
            state=5
        elif(state==7 and ch=='/'):
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
            #print('Mphkaa')
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
            dislayError('Cannot accept nested comments (single line-multiple line comments). Terminating program.')
        elif(state==11 and ch=='/'):
            dislayError('Cannot accept nested single line comments. Terminating program.')
        elif(state==11 and ch==''):
            displayError('File ended without closing comments. Terminating program.')
        elif(state==11 and ch=='\n'):
            fline +=1
            state=0
        elif(state==11 and ch!='*' and ch!='/' and ch!=''):
            state=4
        #elif(state==100):
        #    return
    

#Definition of grammar rules of Starlet#
def block():
    declarations()
    subprograms()
    statements()

def if_stat():
    #if(tokenID == IFTK): #maybe this if is unnecessary
    lex()
    if(tokenID == '('):
        lex()
        condition()
        if(tokenID == ')'):
            lex()
            if(tokenID == 'then'):
                lex()
                statements()
                elsepart()
                print('@@@@@@@@@@@@@@@@@',token, ' ', tokenID)
                if(tokenID == 'endif'):
                    print('Ending if',token, ' ', tokenID)
                    lex()
                    print('After lex endif',token, ' ', tokenID)
                else:
                    displayError('Error15: Expecting binded word "endif", instead of '+ tokenID+'.\nTerminating program')
            else:
                displayError('Error16: Expecting binded word "then", instead of '+ tokenID+'.\nTerminating program')
        else:
            displayError('Error8: Expecting ")", instead of '+ tokenID+'.\nTerminating program')
    else:
        displayError('Error9: Expecting "(", instead of '+ tokenID+'.\nTerminating program')
    #else:
    #    displayError('Error21: Expecting binded word "if". Terminating program') #Not necessary

    
def assignment_stat():
    #if(tokenID == IDTK): #maybe not necessary, use this function after checking statement, same for else statement
    #print('assignment')
    lex()
    print('1',tokenID)
    if(tokenID == ':='):
        #print('assignment1')
        lex()
        print('2',tokenID)
        expression()
    else:
        #print('assignment2')
        displayError('Error14: Expecting assignment operator, instead of '+ tokenID+'.\nTerminating program')
    #else:
    #   displayError('Error16: Expecting variable\'s identifier. Terminating program')        

def statement():
    global indo_while
    if(tokenID == IDTK): #assignment-statement, begin with variable
        assignment_stat()
    if(tokenID == 'if'):
        if_stat()
    if(tokenID == 'while'):
        print('#############')
        if(indo_while):
            indo_while = False
        else:
            while_stat()
    if(tokenID == 'do'):
        print('*************')
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
    #no else, e is permitted

def statements():
    statement()
    while(tokenID == ';'):
        print('Enter multiple statements')
        lex()
        statement()

def elsepart():
    if(tokenID == 'else'):
        lex()
        statements()
    #else not necessary, e is permitted

def while_stat():
    #if(tokenID == WHILETK): #maybe this while is unnecessary
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
    #else:
    #    displayError('Error25: Expecting binded word "while". Terminating program') #Not necessary        

def do_while_stat():
    global indo_while
    indo_while = True
    #if(tokenID == DOTK): #maybe this while is unnecessary
    lex()
    statements()
    if(tokenID == 'while'):
        lex()
        if(tokenID == '('):
            lex()
            condition()
            if(tokenID == ')'):
                lex()
            else:
                displayError('Error8: Expecting ")", instead of '+ tokenID+'.\nTerminating program')
        else:
            displayError('Error9: Expecting "(", instead of '+ tokenID+'.\nTerminating program')
    else:
        displayError('Error18: Expecting binded word "while", instead of '+ tokenID+'.\nTerminating program')
    #else:
    #    displayError('Error29: Expecting binded word "do". Terminating program') #Not necessary

def loop_stat():
    #if(tokenID == LOOPTK): #not necessary?
    lex()
    statements()
    if(tokenID == 'endloop'):
        lex()
    else:
        displayError('Error19: Expecting binded word "endloop", instead of '+ tokenID+'.\nTerminating program')
    #else:
    #    displayError('Error31: Expecting binded word "loop". Terminating program')

def exit_stat():
    #if(tokenID == EXITTK):
    lex()
    #else:
    #    displayError('Error32: Expecting binded word "exit". Terminating program')

def forcase_stat():
    #if(token == 'forcase'):#statements
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
    if(tokenID == 'default'):
        lex()
        if(tokenID == ':'):
            lex()
            statements()
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
    #if(token == incase): #statements
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

def return_stat(): #statements
    #if(token == 'return'):
    lex()
    expression()
    #else:
    #    displayError('Error31: Expecting binded word "return" .Terminating program')

def print_stat(): #statements
    #if(token == 'print'):
    lex()
    expression()
    #else:
    #    displayError('Error32: Expecting binded word "print" .Terminating program')

def input_stat(): #statements
    #if(token == 'input'):
    lex()
    if(tokenID == IDTK):
        lex()
    else:
        displayError('Error25: Expecting input identifier, instead of '+ tokenID+'.\nTerminating program')
    #else:
    #    displayError('Error34: Expecting binded word "input" .Terminating program')

def actualpars():
    #if(tokenID == '('): e is permitted in idtail, look forward to predict
    lex()
    actualparlist()
    if(tokenID == ')'):
        lex()
    else:
        displayError('Error8: Expecting ")", instead of '+ tokenID+'.\nTerminating program')
    #else:
    #    displayError('Error9: Expecting "(", instead of '+ tokenID+'.\nTerminating program')

def actualparlist():
    actualparitem()
    while(tokenID == ','):
        lex()
        actualparitem()

def actualparitem():
    if(tokenID == 'in'):
        lex()
        expression()
    elif(tokenID == 'inout'):
        lex()
        if(tokenID == IDTK):
            lex()
        else:
            displayError('Error11: Expecting variable\'s identifier after inout. Terminating program')
    elif(tokenID == 'inandout'):
        lex()
        if(tokenID == IDTK):
            lex()
        else:
            displayError('Error12: Expecting variable\'s identifier after inandout. Terminating program')
    else:
        displayError('Error13: Expecting parameter\'s type, instead of '+ tokenID+'.\nTerminating program')

def relational_oper():
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

def idtail():
    if(tokenID == '('):
        actualpars()
    #no error, e is permitted
    
def factor():
    if(tokenID == 'constant'):
        lex()
    #else:
    #    displayError('Error28: Expecting binded word "constant" .Terminating program')
    elif(tokenID == '('):
        lex()
        expression()
        if(tokenID == ')'):
            lex()
        else:
            displayError('Error8: Expecting ")", instead of '+ tokenID+'.\nTerminating program')
    #else:
    #    displayError('Error49: Expecting "(" .Terminating program')
    elif(tokenID == IDTK):
        #print('Found id')
        lex()
        #print('Token', tokenID)
        idtail()
    else:
        displayError('Error28: Missing a constant, or a parenthesis or an identifier and nothing matches to what expecting as a factor.\nTerminating program')

def term():
    #print('Token', tokenID)
    factor()
    while(tokenID == '*' or tokenID == '/'):
        #print('enter')
        mul_oper()
        factor()

def expression():
    optional_sign()
    term()
    while(tokenID == '+' or tokenID == '-'):
        add_oper()
        term()

def boolfactor():
    if(tokenID == 'not'):
        lex()
        if(tokenID == '['):
            lex()
            condition()
            if(tokenID == ']'):
                lex()
            else:
                displayError('Error26: Expecting "]", instead of '+ tokenID+'.\nTerminating program')
        else:
            displayError('Error27: Expecting "[", instead of '+ tokenID+'.\nTerminating program')
    #else:
    #    displayError('Error28: Expecting binded word "not", instead of '+ tokenID+'.\nTerminating program')
    elif(tokenID == '['):
        lex()
        condition()
        if(tokenID == ']'):
            lex()
        else:
            displayError('Error26: Expecting "]", instead of '+ tokenID+'.\nTerminating program')
    #else:
    #    displayError('Error27: Expecting "[", instead of '+ tokenID+'.\nTerminating program')
    else:
        expression() #what if the problem goes down to the expressions?
        relational_oper()
        expression()

def boolterm():
    boolfactor()
    while(tokenID == 'and'):
        lex()
        boolfactor()

def condition():
    boolterm()
    while(tokenID == 'or'):
        lex()
        boolterm()
        
def formalparitem():
    if(tokenID == 'in'):
        lex()
        if(tokenID == IDTK):
            lex()
        else:
            displayError('Error10: Expecting variable\'s identifier after in. Terminating program')
    elif(tokenID == 'inout'):
        lex()
        if(tokenID == IDTK):
            lex()
        else:
            displayError('Error11: Expecting variable\'s identifier after inout. Terminating program')
    elif(tokenID == 'inandout'):
        lex()
        if(tokenID == IDTK):
            lex()
        else:
            displayError('Error12: Expecting variable\'s identifier after inandout. Terminating program')
    else:
        displayError('Error13: Expecting parameter\'s type, instead of '+ tokenID+'.\nTerminating program')

def formalparlist():
    formalparitem()
    while(tokenID == ','):
        lex()
        formalparitem()
    #e is permitted - no error

def formalpars():
    if(tokenID == '('):
        lex()
        formalparlist()
        if(tokenID == ')'):
            lex()
        else:
            displayError('Error8: Expecting ")", instead of '+ tokenID+'.\nTerminating program')
    else:
        displayError('Error9: Expecting "(", instead of '+ tokenID+'.\nTerminating program')
    
def funcbody():
    formalpars()
    block()

def subprogram():
    #if(tokenID=='function'): #already checked in subprograms
    lex()
    if(tokenID==IDTK):
        lex()
        funcbody()
        if(tokenID == 'endfunction'):
            lex()
        else:
            displayError('Error6: Expecting binded word "endfunction", instead of '+ tokenID+'\nTerminating program')
    else:
        displayError('Error7: Expecting function\'s identifier, instead of '+ tokenID+'\nTerminating program')
    #else:
    #    displayError('Error8: Expecting binded word "function", instead of '+ tokenID+'\nTerminating program')

def subprograms():
    while(tokenID=='function'):
        subprogram()

def varlist():
    if(tokenID == IDTK):
        lex()
        while(tokenID == ','):
            lex()
            if(tokenID == IDTK):
                lex()
            else:
                displayError('Error5: Expecting identifier after comma. Terminating program')
    # else is not necessary, e is permitted

def declarations():
    while(tokenID=='declare'):
        lex()
        varlist()
        if(tokenID == ';'):
            lex()
        else:
            displayError('Error4: Expecting ";", instead of '+ tokenID+'\nTerminating program')

def program():
    lex() #lexical analyzer - first rule, need to "fill" token
    if(tokenID == 'program'):
        lex()
        if(tokenID == IDTK):
            lex()
            block()
            if(tokenID == 'endprogram'):
                lex() #expecting eof, or check for sth else
            else:
                displayError('Error1: Expecting binded word "endprogram", instead of '+ tokenID+'\nTerminating program')
        else:
            displayError('Error2: Expecting program\'s identifier, instead of "'+ tokenID+'"\nTerminating program')
    else:
        displayError('Error3: Expecting binded word "program", instead of "'+ tokenID+'"\nTerminating program')


#-----Main function-----#
f = open('test1.stl', 'r')
program()
print(tokenID)
if(not (endOfFile or tokenID=='EOF')):
    print('Redundant characters after "endprogram". Please remove everything else except any comments')
else:
    print('Compilation ended successfully!');
f.close()
