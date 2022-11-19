from intbase import InterpreterBase


class FunctionManager:
  def __init__(self):
    self.function_defs = {}
    self.call_stack = []
    self.function_stack = []
    self.current_function = None

  def store_functions(self,tokenized_program):
    for index in range(len(tokenized_program)):
      statement = tokenized_program[index]
      if(statement[0] == InterpreterBase.FUNC_DEF):
        function_name = statement[1]
        num_parameters = len(statement[2:-1])
        return_type = statement[-1]
        # TODO: Check for references 
        parameter_types = []
        for pair in statement[2:-1]:
          pair = pair.split(':')
          name = pair[0]
          vtype = pair[1]
          if("ref" in vtype):
            parameter_types.append((name,vtype[3:],"ref"))
          else:
            parameter_types.append((name,vtype))
        self.function_defs[function_name] = {
          "line_num" : index,
          "num_parameters" : num_parameters,
          "parameter_types" : parameter_types,
          "return_type" : return_type
        }
      
  def get_current_function(self):
    return self.function_stack[-1]

  def get_line_num(self,function_name):
    return self.function_defs[function_name]["line_num"]

  def get_return_type(self,function_name):
    return self.function_defs[function_name]["return_type"]

  def get_num_parameters(self,function_name):
    return self.function_defs[function_name]["num_parameters"]

  def get_parameters(self,function_name):
    return self.function_defs[function_name]["parameter_types"]
  
  def function_present(self,function_name):
    if(function_name not in self.function_defs):
      return False
    else:
      return True
  
  def update_stacks(self,call_stack_elem, function_stack_elem):
    self.call_stack.append(call_stack_elem)
    self.function_stack.append(function_stack_elem)
  
  def pop_stack(self):
    call_return = self.call_stack.pop()
    self.function_stack.pop()
    return call_return