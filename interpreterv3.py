from enum import Enum
from intbase import InterpreterBase
from intbase import ErrorType
from tokenize import Tokenizer
from scope import ScopeManager
from func import FunctionManager
import operator


class Interpreter(InterpreterBase):
  
  #constants
  VALUE = 0
  TYPE = 1

  # Interpreter Constructor
  def __init__(self, console_output=True, input=None, trace_output=False):
    super().__init__(console_output, input)



    # Object Members
    self.tokenizer = Tokenizer()
    self.scope = ScopeManager()
    self.functions = FunctionManager()

    # Map of conditional branches and jumps
    self.conditional_map = {}
    # Dictionary storing function names and line
    self.variables = {}
    # Tokenized program code
    self.program_code = []
    # Inbuilt function
    self.inbuilt_functions = {self.PRINT_DEF,
                              self.STRTOINT_DEF, self.INPUT_DEF}
  
    # Variable Types
    self.types = {self.INT_DEF,self.STRING_DEF,self.BOOL_DEF}

    # Integer operators
    self.int_ops = {
        '+': operator.add,
        '-': operator.sub,
        '*': operator.mul,
        '/': operator.floordiv,  # use operator.div for Python 2
        '%': operator.mod,
        '<': operator.lt,
        '>': operator.gt,
        '<=': operator.le,
        '>=': operator.ge,
        '!=': operator.ne,
        '==': operator.eq,
    }
    # String Operators
    self.str_ops = {
        '+': operator.add,
        '<': operator.lt,
        '>': operator.gt,
        '<=': operator.le,
        '>=': operator.ge,
        '!=': operator.ne,
        '==': operator.eq,
    }
    # Bool Operators
    self.bool_ops = {
        '!=': operator.ne,
        '==': operator.eq,
        '&': lambda a, b: a and b,
        '|': lambda a, b: a or b,
    }


  def run(self, program):
    """This is the primary function in the interpreter that executes Brewin code

    Args:
        program ([string]): Program stored in a list of strings
    """
    # Stores tokenized program code in self.program_code
    self.store_program(program)
    # Set up function informations
    self.functions.store_functions(self.program_code)
    # Set instruction pointer to first line of main
    self.instruction_poiner = self.functions.get_line_num(self.MAIN_FUNC)
    self.functions.update_stacks(call_stack_elem=self.MAIN_FUNC, function_stack_elem= self.MAIN_FUNC)
    # Add main function scope and main's local scope
    self.scope.function_scopes.append([{}])

    # We run until we reach end of main
    while (True):
      # Sanity check
      if (self.instruction_poiner >= self.total_lines):
        break
      # Read a statement
      statement = self.program_code[self.instruction_poiner]

      # Match first token
      match statement[0]:

        case self.VAR_DEF:
          self.evaluate_var(statement)

        # Assign value to a variable
        case self.ASSIGN_DEF:
          self.evaluate_assign(statement)

        # Function Call
        case self.FUNCCALL_DEF:
          self.evaluate_funccall(statement)

        # Function definition
        case self.FUNC_DEF:
          self.evaluate_func(statement)

        # End Function
        case self.ENDFUNC_DEF:
          continue_execution = self.evaluate_endfunc(statement)
          if (not continue_execution):
            return

        # If block starts
        case self.IF_DEF:
          self.evaluate_if(statement)

        # Else block starts
        case self.ELSE_DEF:
          self.evaluate_else(statement)

        # If-Else block ends
        case self.ENDIF_DEF:
          self.evaluate_endif(statement)

        # While loop starts
        case self.WHILE_DEF:
          self.evaluate_while(statement)

        # While loop ends
        case self.ENDWHILE_DEF:
          self.evaluate_endwhile(statement)

        # Return from function and store value in result
        case self.RETURN_DEF:
          continue_execution = self.evaluate_return(statement)
          if (not continue_execution):
            return
        
        case _:
          # Should never reach here except empty lines, other cases are syntax errors!
          self.instruction_poiner += 1
    

  def evaluate_var(self,statement):
    # Varaible type
    var_type = statement[1]
    # Check if unknown type
    if(var_type not in self.types):
      self.error(ErrorType.TYPE_ERROR, "Variable type is wrong", self.instruction_poiner)
    var_names = statement[2:]
    for var_name in var_names:
      # Check if var not in current scope already
      if(self.scope.check_in_local_scope(var_name)):
        self.error(ErrorType.NAME_ERROR,"Duplicate variable definitions within the same block", self.instruction_poiner)
      else:
        match var_type:
          case self.STRING_DEF:
            self.scope.add_to_local_scope(var_name,("",var_type))
          case self.INT_DEF:
            self.scope.add_to_local_scope(var_name,(0,var_type))
          case self.BOOL_DEF:
            self.scope.add_to_local_scope(var_name,(False,var_type))
    self.instruction_poiner += 1

  def evaluate_assign(self, statement):
    """Evaluates an assign statement

    Args:
        statement ([string]): A tokenized statement
    """
    # Evaluate expression
    evaluation_result = self.evaluate_expression(statement[2:])
    variable_name = statement[1]
    # Check if variable in any scope
    if(not self.scope.check_in_function_scope(variable_name)):
      self.error(ErrorType.NAME_ERROR, "Variable not found", self.instruction_poiner)
    
    # Get variable type from scope
    index = self.scope.find_scope_num(variable_name)
    variable_type = self.scope.get_variable(index,variable_name)[self.TYPE]
    # Check type
    if(variable_type != evaluation_result[self.TYPE]):
      self.error(ErrorType.TYPE_ERROR, "Variable type is different than value assigned", self.instruction_poiner)
    # Set variable
    self.scope.set_variable(index,variable_name,evaluation_result)
    self.scope.set_referenced(variable_name)
    self.instruction_poiner += 1


  def evaluate_funccall(self, statement):
    """Evaluates an funccall statement

    Args:
        statement ([string]): A tokenized statement
    """
    # TODO:
    # print(self.scope.function_scopes)
    function_name = statement[1]
    # If inbuilt function
    if (function_name in self.inbuilt_functions):
      self.execute_inbuilt_function(statement)
    else:
      # Sanity check for undefined functions
      if (not self.functions.function_present(function_name)):
        self.error(
            ErrorType.NAME_ERROR, f"Function {function_name} not defined ", self.instruction_poiner)
   
      # Passed parameters
      passed_parameter_names = statement[2:]
      passed_parameters = list(map(lambda parameter: self.parse_value_type(parameter),statement[2:]))
      # Getting the formal parameters of the function
      formal_parameters = self.functions.get_parameters(function_name)
      
      # Check number of parameters matching
      if(len(passed_parameters) != self.functions.get_num_parameters(function_name)):
        self.error(ErrorType.NAME_ERROR,"Wrong number of parameters",self.instruction_poiner)
      
      # Adding new function_scope for function called 
      self.scope.function_scopes.append([{}])
      for index in range(len(passed_parameters)):
        
        # Parsing type of passed parameter
        passed_parameter = passed_parameters[index]
        passed_parameter_name = passed_parameter_names[index]
        passed_parameter_type = passed_parameter[self.TYPE]
        
        # Parsing type of formal parameter
        formal_parameter = formal_parameters[index]
        formal_parameter_name = formal_parameter[0]
        formal_parameter_type = formal_parameter[1]
        
        # For pass by reference, the passed parameter must be a variable
        is_passed_parameter_variable = self.scope.check_in_function_scope(passed_parameter_name,-2)
        is_formal_parameter_reference = True if len(formal_parameter) == 3 else False
        pass_by_reference = is_passed_parameter_variable and is_formal_parameter_reference
 
        # Checking type compatability
        if(passed_parameter_type != formal_parameter_type):
          self.error(ErrorType.TYPE_ERROR,"Wrong type of Parameters", self.instruction_poiner)
        
        # Checking if pass-by-reference
        if(pass_by_reference):
          self.scope.add_to_local_scope(formal_parameter_name,(passed_parameter[self.VALUE],passed_parameter[self.TYPE],passed_parameter_name))
        else:
          self.scope.add_to_local_scope(formal_parameter_name,(passed_parameter[self.VALUE],passed_parameter[self.TYPE]))

      # Add next line to call stack and jump to called function
      self.functions.update_stacks(call_stack_elem=self.instruction_poiner + 1, function_stack_elem=function_name)
      self.instruction_poiner = self.functions.get_line_num(function_name)


  def evaluate_func(self, statement):
    """Evaluates an func statement

    Args:
        statement ([string]): A tokenized statement
    """
    self.instruction_poiner += 1


  def evaluate_endfunc(self, statement):
    """Evaluates an endfunc statement

    Args:
        statement ([string]): A tokenized statement
    Returns:
        (bool): True if program should continue, False to exit
    """
    if (len(self.functions.call_stack) > 1):
      required_return_type = self.functions.get_return_type(self.functions.get_current_function())
      self.return_default_values(required_return_type)
      self.instruction_poiner = self.functions.pop_stack()
      self.scope.function_scopes.pop()
      return True
    # If call_stack just has "main" and we reach endfunc, exit
    else:
      return False


  def evaluate_if(self, statement):
    """Evaluates an if statement

    Args:
        statement ([string]): A tokenized statement
    """
    result = self.evaluate_expression(statement[1:])
    # If expression doesn't return bool give TYPE_ERROR
    if ( result[self.TYPE] != self.BOOL_DEF ):
      self.error(ErrorType.TYPE_ERROR,
                 "Expression result is not a bool", self.instruction_poiner)
    if (result[self.VALUE] == True):
      self.scope.add_new_scope()
      self.instruction_poiner += 1
      
    else:
      # Go to else + 1
      if_map = self.conditional_map[self.instruction_poiner]
      # If there's an else only then add a scope
      if(len(if_map) == 2):
        self.scope.add_new_scope()
      self.instruction_poiner = if_map[0] + 1


  def evaluate_else(self, statement):
    """Evaluates an else statement

    Args:
        statement ([string]): A tokenized statement
    """
    # If we reach here, then if stmt was true, go to endif
    self.instruction_poiner = self.conditional_map[self.instruction_poiner][0]


  def evaluate_endif(self, statement):
    """Evaluates an endif statement

    Args:
        statement ([string]): A tokenized statement
    """
    self.scope.delete_current_scope()
    self.instruction_poiner += 1


  def evaluate_while(self, statement):
    """Evaluates a while statement

    Args:
        statement ([string]): A tokenized statement
    """
    result = self.evaluate_expression(statement[1:])
    # If expression doesn't return bool give TYPE_ERROR
    if (result[self.TYPE] != self.BOOL_DEF):
      self.error(ErrorType.TYPE_ERROR,
                 "Expression result is not a bool", self.instruction_poiner)
    if (result[self.VALUE] == True):
      self.scope.add_new_scope()
      self.instruction_poiner += 1
    else:
      self.instruction_poiner = self.conditional_map[self.instruction_poiner] + 1


  def evaluate_endwhile(self, statement):
    """Evaluates an endwhile statement

    Args:
        statement ([string]): A tokenized statement
    """
    self.scope.delete_current_scope()
    self.instruction_poiner = self.conditional_map[self.instruction_poiner]


  def evaluate_return(self, statement):
    """Evaluates a return statement

    Args:
        statement ([string]): A tokenized statement
    Returns:
        (bool): True if program should continue, False to exit
    """
    # Setting results
    if (len(self.functions.call_stack) == 1):
      return False

    required_return_type = self.functions.get_return_type(self.functions.get_current_function())
    
    if (len(statement) > 1):
      return_value_type = self.evaluate_expression(statement[1:])
      if(return_value_type[self.TYPE] != required_return_type):
        self.error(ErrorType.TYPE_ERROR,"Wrong return type",self.instruction_poiner)
      else:
        # Setting result in top scope of calling function
        self.scope.set_result(-2,return_value_type)
    else:
      self.return_default_values(required_return_type)

    self.instruction_poiner = self.functions.pop_stack()
    self.scope.function_scopes.pop()
    return True

    
  def return_default_values(self,return_type):
    if (return_type == self.STRING_DEF):
      self.scope.set_result(-2,("",self.STRING_DEF))
    elif (return_type == self.INT_DEF):
      self.scope.set_result(-2,(0,self.INT_DEF))
    elif (return_type == self.BOOL_DEF):
      self.scope.set_result(-2,(False,self.BOOL_DEF))
    else:
      pass

  def execute_inbuilt_function(self, statement):
    """Executes an inbuilt function

    Args:
        statement ([string]): A tokenized statement
    """
    function_name = statement[1]
    match function_name:
      # Inbuilt print funtion
      case self.PRINT_DEF:
        output_str = "".join(
            list(map(lambda token: str(self.parse_value_type(token)[self.VALUE]), statement[2:])))
        self.output(output_str)

      # Inbuilt input function
      case self.INPUT_DEF:
        output_str = "".join(
            list(map(lambda token: str(self.parse_value_type(token)[self.VALUE]), statement[2:])))
        self.output(output_str)
        input = self.get_input()
        self.scope.set_result(-1,(input,self.STRING_DEF))

      # Inbuilt strtoint function
      case self.STRTOINT_DEF:
        parsed_value = self.parse_value_type(statement[2])
        if (parsed_value[self.TYPE] != self.STRING_DEF):
          self.error(
              ErrorType.TYPE_ERROR, "Passed value is not a string", self.instruction_poiner)
        else:
          self.scope.set_result(-1,(int(parsed_value[self.VALUE]),self.INT_DEF))

      case _:
        pass
    self.instruction_poiner += 1


  def evaluate_expression(self, expression):
    """Evaluate an expression a variable or a constant

    Args:
        expression ([string]): A tokenized expression

    Returns:
        result: Result of expression evaluation
    """
    # Reverse the expressions to push into stack
    expression.reverse()
    stack = []
    if (len(expression) < 1):
      self.error(ErrorType.SYNTAX_ERROR, "Empty expression",
                 self.instruction_poiner)
    for i in range(len(expression)):
      token = expression[i]
      # If token is an operation, pop2 -> evaluate ->push
      if (token in self.int_ops or token in self.str_ops or token in self.bool_ops):
        # Checks if operands are of correct types\
        if(len(stack) < 2):
          self.error(ErrorType.SYNTAX_ERROR, "Invalid Expression Syntax", self.instruction_poiner)
        operand1 = stack[-1]
        operand2 = stack[-2]

        if (operand1[self.TYPE] != operand2[self.TYPE]):
          self.error(
              ErrorType.TYPE_ERROR, "Operand types do not match", self.instruction_poiner)
        # Uses correct operator type on the operand
        if (operand1[self.TYPE] == self.STRING_DEF and token in self.str_ops):
          evaluated = self.str_ops[token](operand1[self.VALUE], operand2[self.VALUE])
        elif (operand1[self.TYPE] == self.INT_DEF and token in self.int_ops):
          evaluated = self.int_ops[token](operand1[self.VALUE], operand2[self.VALUE])
        elif (operand1[self.TYPE] == self.BOOL_DEF and token in self.bool_ops):
          evaluated = self.bool_ops[token](operand1[self.VALUE], operand2[self.VALUE])
        else:
          self.error(
              ErrorType.TYPE_ERROR, "Operator doesn't match operand type", self.instruction_poiner)
        stack = stack[:-2]
        stack.append((evaluated, self.get_type_value(evaluated)))

      # Else push the operand on stack after parsing value
      else:
        parsed_operand = self.parse_value_type(token)
        stack.append(parsed_operand)
    result = stack.pop()
    return result

    
  def get_type_value(self,value):
    if(type(value) == int):
      return self.INT_DEF
    elif(type(value) == str):
      return self.STRING_DEF
    elif(type(value) == bool):
        return self.BOOL_DEF
    else:
      return None

  # Parses constants and variables to get the value and type
  def parse_value_type(self, token):
    """Parses a token to give its barebones form

    Args:
        token (string): Lexical token

    Returns:
        token_value: Value of the token
    """
    if (token[0] == token[-1] == '\"'):
      return (token[1:-1],self.STRING_DEF)
    elif (token.lstrip('-').isnumeric()):
      return (int(token),self.INT_DEF)
    elif (token == "True"):
      return (True, self.BOOL_DEF)
    elif (token == "False"):
      return (False, self.BOOL_DEF)
    elif (self.scope.find_scope_num(token) != -1):
      index = self.scope.find_scope_num(token)
      variable = self.scope.get_variable(index,token)
      if (variable[self.VALUE] == None):
        self.error(ErrorType.SYNTAX_ERROR,"Variable not assigned any value", self.instruction_poiner)
      return variable
    else:
      return self.error(ErrorType.NAME_ERROR, "Invalid token, variable not found", self.instruction_poiner)


  # Reads the input and stores a tokenized version of the code
  def store_program(self, program):
    """Converts the list of statements to a tokenized version

    Args:
        program ([string]): A list of stements
    """
    for line in program:
      line = line.lstrip()  # Removing leading whitespace
      line = line.rstrip()  # Removing trailing whitespace
      self.program_code.append(line)

    # Total number of lines on the program
    self.total_lines = len(self.program_code)
    if_stack = []
    while_stack = []
    for index in range(self.total_lines):
      line = self.program_code[index]
      tokenized_line = self.tokenizer.tokenize(line)

      # Replacing line string with tokenized version
      self.program_code[index] = tokenized_line
      match tokenized_line[0]:

        case self.IF_DEF:
          if_stack.append([index])

        case self.ELSE_DEF:
          if_stack[-1].append(index)

        case self.ENDIF_DEF:
          last_if = if_stack.pop()
          last_if.append(index)
          # Setting map from if to else and endif
          if_line = last_if[0]
          others = last_if[1:]
          self.conditional_map[if_line] = others
          # Setting map from else to endif
          if (len(others) == 2):
            self.conditional_map[others[0]] = [others[1]]

        case self.WHILE_DEF:
          while_stack.append(index)

        case self.ENDWHILE_DEF:
          last_while = while_stack.pop()
          self.conditional_map[last_while] = index
          self.conditional_map[index] = last_while

