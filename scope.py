from intbase import InterpreterBase

class ScopeManager:
  def __init__(self):
    self.function_scopes = []
    # self.reference_variables_stack = []



  # Find the scope number of a varaible in a given function scope
  def find_scope_num(self, variable_name, function_scope_stack_index = -1):
    function_scope_stack = self.function_scopes[function_scope_stack_index]
    for index in reversed(range(len(function_scope_stack))):
      if(variable_name in function_scope_stack[index]):
        return index
    return -1 


  # Add a variable to the local scope of the current function scope
  def add_to_local_scope(self,variable_name,value_type,function_scope_stack_index=-1):
    function_scope_stack = self.function_scopes[function_scope_stack_index]
    function_scope_stack[-1][variable_name] = value_type


  # Check if a variable is in the local scope
  def check_in_local_scope(self,variable_name):
    function_scope_stack = self.function_scopes[-1]
    if(variable_name in function_scope_stack[-1]):
      return True
    else:
      return False
 
  def check_in_function_scope(self,variable_name,function_scope_stack_index=-1):
    function_scope_stack = self.function_scopes[function_scope_stack_index]
    for scope in function_scope_stack:
      if(variable_name in scope):
        return True
    return False


  # Get a varaible value_type given scope_index and variable_name
  def get_variable(self,scope_index,name):
    function_scope_stack = self.function_scopes[-1]
    return function_scope_stack[scope_index][name]

  # Set a variable valu_type given scope_index and variable_na
  def set_variable(self,scope_index,name,result):
    # If result has reference, we still want to assign by value
    value = result[0]
    vtype = result[1]
    result = (value,vtype)

    function_scope_stack = self.function_scopes[-1]
    if(len(function_scope_stack[scope_index][name]) == 3):
      reference = function_scope_stack[scope_index][name][2]
      result = result + (reference,)
    function_scope_stack[scope_index][name] = result
  


  def add_new_scope(self):
    self.function_scopes[-1].append({})

  def delete_current_scope(self):
    self.function_scopes[-1].pop()

  def set_result(self,index,value_type):
    previous_function_scope_stack = self.function_scopes[index]
    top_scope = previous_function_scope_stack[0]
    value = value_type[0]
    vtype = value_type[1]
    match vtype:
      case InterpreterBase.STRING_DEF:
        top_scope["results"] = (value,vtype)
      case InterpreterBase.INT_DEF:
        top_scope["resulti"] = (value,vtype)
      case InterpreterBase.BOOL_DEF:
        top_scope["resultb"] = (value,vtype)

  def set_referenced(self,variable_name,function_scope_stack_index=-1):
    current_function_scope_stack = self.function_scopes[function_scope_stack_index]
    index = self.find_scope_num(variable_name)
    scope = current_function_scope_stack[index]
    value_type = scope[variable_name]
    if(len(value_type) == 3):
      value = value_type[0]
      vtype = value_type[1]
      referenced_name = value_type[2]
      
      previous_function_scope_stack = self.function_scopes[function_scope_stack_index-1]
      var_scope_index = self.find_scope_num(referenced_name,function_scope_stack_index-1)
      var_scope = previous_function_scope_stack[var_scope_index]
      
      if(len(var_scope[referenced_name]) == 3):
        reference = var_scope[referenced_name][2]
        var_scope[referenced_name] = (value,vtype,reference)
        # Recursively update all referenced variables
        self.set_referenced(referenced_name,function_scope_stack_index-1)
      else:
        var_scope[referenced_name] = (value,vtype)

      # Update all reference variables in the current stack
      self.update_from_referenced(function_scope_stack_index)
          
  
  def update_from_referenced(self,function_scope_stack_index=-1):
    current_function_scope_stack = self.function_scopes[function_scope_stack_index]
    for scope in current_function_scope_stack:
      for variable in scope:
        value_type = scope[variable]
        if(len(value_type) == 3):
          # Scope of referenced variable
          previous_function_scope_stack = self.function_scopes[function_scope_stack_index-1]
          referenced_name = value_type[2]
          var_scope_index = self.find_scope_num(referenced_name,function_scope_stack_index-1)
          var_scope = previous_function_scope_stack[var_scope_index]
          
          referenced_value = var_scope[referenced_name][0]
          referenced_type = var_scope[referenced_name][1]

          scope[variable] = (referenced_value,referenced_type,referenced_name)

     
    