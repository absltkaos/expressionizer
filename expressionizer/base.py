import re
import logging

class BaseExpression:
    """
    This is a base class for others to inherit from
    """
    default_operators={
            'group_start_char': '(',
            'group_end_char': ')',
            'not_operators': ['!'],
            'and_operators': ['&'],
            'or_operators': ['|'],
            'sub_expressions': {},
    }
    def __init__(self,operators=None,logger=None):
        """
        Initialize the expression with the given operators. The "operators"
        argument is a dictionary. The not_operators,and_operators, and
        or_operators are all lists. The group_start_char and group_end_char
        are both single character strings.

        Args:
            operators       Dict of operators
        """
        self.logger = logger or logging.getLogger(self.__class__.__name__)
        if not operators:
            self.operators=self.default_operators
        else:
            self.operators=operators
    def _indent_lvl(self,lvl):
        """
        This is a helper function that generates a string of spaces based.

        Args:
            lvl     Int indicating the number of spaces to use

        Returns:
            String
        """
        i_lvl=''
        for i in range(lvl):
            i_lvl+=' '
        return i_lvl
    def _allOps(self):
        """
        Process all of the operators in self.operators and return a combined
        list of all of them

        Args:
            None

        Returns:
            List of all operators found
        """
        ops=[]
        for op_type in self.operators.keys():
            if op_type == 'sub_expressions':
                continue
            for op in self.operators[op_type]:
                ops.append(op)
        ops+=self._subExprOps()
        return ops
    def _subExprOps(self):
        """
        Returns:
            List        List of all sub expression operators
        """
        ops=[]
        if self.operators['sub_expressions']:
            for sek in self.operators['sub_expressions']:
                ops.append(self.operators['sub_expressions'][sek]['start_char'])
                ops.append(self.operators['sub_expressions'][sek]['end_char'])
        return ops
    def _getSubExprDetail(self,op=None,name=None):
        """
        Takes an operator character and loads up the sub expression detail if
        found.

        Args:
            op      String that is a single character representing the sub
                    expression operator
            name    String representing the name of the subexpression
        Returns:
            Tuple, where first element is the start_char, second is end_char,
            third is the function, fourth is the name of the subexpression
        """
        detail=()
        if not op and not name:
            raise ValueError("Must have either op, or name defined to load subexpression detail")
        if name:
            try:
                start_char=self.operators['sub_expressions'][name]['start_char']
                end_char=self.operators['sub_expressions'][name]['end_char']
                func=self.operators['sub_expressions'][name]['func']
                s_name=name
                detail=(start_char,end_char,func,s_name)
            except KeyError:
                pass
        if self.operators['sub_expressions']:
            for sek in self.operators['sub_expressions']:
                start_char=self.operators['sub_expressions'][sek]['start_char']
                end_char=self.operators['sub_expressions'][sek]['end_char']
                func=self.operators['sub_expressions'][sek]['func']
                s_name=sek
                if op in [ start_char, end_char ]:
                    detail=(start_char,end_char,func,s_name)
                    break
        return detail
    def _nextOp(self,expression):
        """
        Take a given expression in list format and find the next operator with
        its location

        Args:
            expression      String representing an expression

        Returns:
            Tuple, where 1st element is a string of the operator found 2nd is 
                a number, that is the location of the operator, and third is the
                length of the operator
        """
        n_op={}
        ops=self._allOps()
        for op in ops:
            loc=expression.find(op)
            if loc >= 0:
                n_op[loc]=op
        #Find the earliest operator
        n_op_locs=list(n_op.keys())
        n_op_locs.sort()
        if n_op_locs:
            return (n_op[n_op_locs[0]],n_op_locs[0],len(n_op[n_op_locs[0]]))
        else:
            return (None, None, None)
    def _nextOpLi(self,expression_list):
        """
        Take a given expression in list format and find the next operator with
        its location

        Args:
            expression      List representing an expression

        Returns:
            Tuple, where 1st element is a string of the operator found 2nd is 
                a number, that is the item location of the operator in
                expression_list
        """
        nop=None
        loc=None
        ops=self._allOps()
        count=0
        for item in expression_list:
            if item in ops:
                nop=item
                loc=count
                break
            count+=1
        return (nop, loc)
    def _tokenizer(self,expression):
        """
        Take an expression and split it into nouns and verbs(operators)

        Args:
            expression      String with the expression to the process

        Returns:
            List where each element is either a noun or an operator
        """
        cur_expression=expression
        lhs=[]
        while cur_expression:
            next_op=self._nextOp(cur_expression)
            if not next_op[0]:
                lhs.append(cur_expression)
                cur_expression=''
            else:
                noun=cur_expression[:next_op[1]]
                cur_expression=cur_expression[next_op[1]+next_op[2]:]
                if noun:
                    lhs.append(noun)
                lhs.append(next_op[0])
        return (lhs)
    def _evalExpression(expression,subExprName=None,recurse_lvl=0):
        """
        Returns a Set with the give name as the argument

        Args:
            name    Name that gets translated into a set, the expression uses
        """
        raise NotImplementedError
    def addSubExpression(self,name,start_char,end_char,func,all_name):
        """
        Add a new subexpression group to the operators dictionary. This allows
        different kinds of nouns to be retrieved and combined with.
        
        Start_char cannot be the same as end_char

        Args:
            name        String with the name of the subexpression
            start_char  Single String character indicating the start of when
                        this subexpression starts
            end_char   Single String character indicating the end of the sub
                        expression
            func        Function to pass nouns to.
            all_name    String that is a noun to indicate the whole superset. 
                        Used when using the _notWrapGrouper function.
        Returns:
            None
        """
        if start_char == end_char:
            raise ValueError("start_char cannot be the same as end_char: %s == %s" %(start_char,end_char))
        self.operators['sub_expressions'][name]={}
        self.operators['sub_expressions'][name]['start_char']=start_char
        self.operators['sub_expressions'][name]['end_char']=end_char
        self.operators['sub_expressions'][name]['func']=func
        self.operators['sub_expressions'][name]['all_name']=all_name
    def processExpression(self,expression):
        """
        This uses _evalExpression to return the resulting Set. This is the
        primary function that should be used.

        Args:
            expression      String representing an expression to process

        Returns:
            Set from the results of processing.
        """
        result=self._evalExpression(expression)
        return result[0]
    def getVal(self,name):
        """
        Returns a Set with the give name as the argument

        Args:
            name    Name that gets translated into a set, the expression uses
        """
        raise NotImplementedError

class BaseSetExpression(BaseExpression):
    """
    This is a base class for others to inherit from for performing
    combining lists into Sets.
    """
    default_all_name='all'
    def __init__(self,operators=None,all_name=None):
        """
        Initialize the expression with the given operators. The "operators"
        argument is a dictionary. The not_operators,and_operators, and
        or_operators are all lists. The group_start_char and group_end_char
        are both single character strings.

        Args:
            operators       Dict of operators
        """
        self.logger = logger or logging.getLogger(self.__class__.__name__)
        if not operators:
            self.operators=self.default_operators
        else:
            self.operators=operators
        if not all_name:
            self.all_name=self.default_all_name
        else:
            self.all_name=all_name
    def _combineSets(self,left_set,op,right_set):
        """
        Take two Set objects and combine with either an or,and, or not operator

        Args:
            left_set    First Set to be combined with second Set
            op          String of the Operator to be used to combine the two sets
            right_set   Second Set to be combined with First Set

        Returns:
            Set that is the result combining the two Sets.
        """
        #print("combineSets opts: %s %s %s" % (str(left_set),op,str(right_set)))
        result_set=set()
        if op in self.operators['and_operators']:
            result_set=left_set.intersection(right_set)
        elif op in self.operators['or_operators']:
            result_set=left_set.union(right_set)
        elif op in self.operators['not_operators']:
            result_set=left_set.difference(right_set)
        else:
            raise ValueError("Unknown operator: %s" % (op))
        #print("combineSets returning: %s" % (str(result_set)))
        return result_set
    def _notWrapGrouper(self,expression,subExprName=None):
        """
        Take an expression and wrap parts that have the "not" operator with
        grouping chars against the 'all' operator for getSet functions.

        Args:
            expression      String or List with the expression to process

        Returns:
            Tuple, where the first element is a List that is a the processed 
            expression, and the second is a List with remaining expression
            to process (Only really useful when recursing, otherwise is empty)
        """
        lhs=[]
        ops=self._allOps()
        all_name=self.all_name
        if isinstance(expression,str):
            tokens=self._tokenizer(expression)
        else:
            #Assume a List was passed
            tokens=expression
        sub_expression_ops=self._subExprOps()
        not_op_set=False
        if subExprName:
            cur_s_expr=self._getSubExprDetail(name=subExprName)
            all_name=cur_s_expr[3]
        while tokens:
            t=tokens.pop(0)
            if t not in ops:
                lhs.append(t)
            else:
                if t in self.operators['not_operators']:
                    lhs.append(self.operators['group_start_char'])
                    lhs.append(all_name)
                    lhs.append(self.operators['and_operators'][0])
                    not_op_set=True
                if t in sub_expression_ops:
                    #token is part of a sub expression, look up its details
                    s_expr=self._getSubExprDetail(t)
                    s_expr_start=s_expr[0]
                    s_expr_end=s_expr[1]
                    s_expr_allname=s_expr[3]
                    s_expr_name=s_expr[4]
                    #Check if we are currently withing a sub expression:
                    if subExprName:
                        s_expr_end=cur_s_expr[1]
                    if t == s_expr_start:
                        #Recursion!
                        lhs.append(t)
                        rec_result=self._notWrapGrouper(''.join(tokens),subExprName=s_expr_name)
                        lhs+=rec_result[0]
                        tokens=rec_result[1]
                        if not_op_set:
                            lhs.append(self.operators['group_end_char'])
                            not_op_set=False
                        continue
                    if t == s_expr_end:
                        lhs.append(t)
                        break
                elif t == self.operators['group_start_char']:
                    #Recursion!
                    lhs.append(t)
                    rec_result=self._notWrapGrouper(''.join(tokens),subExprName=subExprName)
                    lhs+=rec_result[0]
                    tokens=rec_result[1]
                    if not_op_set:
                        lhs.append(self.operators['group_end_char'])
                        not_op_set=False
                elif t == self.operators['group_end_char']:
                    lhs.append(t)
                    break
                else:
                    lhs.append(t)
        if not_op_set:
            lhs.append(self.operators['group_end_char'])
            not_op_set=False
        return(lhs,tokens)
    def _evalExpression(self,expression,wrap_grouper=True,subExprName=None,recurse_lvl=0):
        """
        Evaluate an expression and pass to _combineSets etc...
        This does all of the heavy lifting and parsing etc...

        Args:
            expresssion     String or List representing the expression to process
            wrap_grouper    Bool indicating whether or not the expression
                            should be run through _notWrapGrouper
            subExprName     String that is the 'name' of the subexpression
                            to use for getSet function. Mostly used internally
                            when recursing
            recurse_lvl     This indicates the depth of the recusion. Only used
                            internally.

        Returns:
            Tuple, first element is the resulting Set object, second element is
            a String of any remaning bits of a expression that needs to be
            processed (only used when recursing because of group operators)
        """
        wrap_group=wrap_grouper
        sub_expression_ops=self._subExprOps()
        ops=self._allOps()
        #indent_str=self._indent_lvl(recurse_lvl)
        #Convert expression from string to token List if passed as a String
        if isinstance(expression,str):
            tokens=self._tokenizer(expression)
        else:
            #Assume a List was passed
            tokens=expression
        #Wrap expression in group chars when not operator found
        if wrap_group:
            tokens=self._notWrapGrouper(tokens)[0]
            wrap_group=False
        lhs=set()
        last_op=''
        #Load up subexpression information within recursion
        if subExprName:
            cur_s_expr=self._getSubExprDetail(name=subExprName)
            getSetFunc=cur_s_expr[2]
            name_pref=subExprName
        else:
            getSetFunc=self.getSet
            name_pref='Base'
        #print("%s%s:tokens=%s" %(indent_str,name_pref,''.join(tokens)))
        #Loop through all our items
        while tokens:
            t=tokens.pop(0)
            if t not in ops:
                #token is a name/noun, so convert it to a list, and combine if needed
                if last_op:
                    #print("%s%s:Combining left hand side. op=%s, noun=%s" % (indent_str,name_pref,last_op,t))
                    lhs=self._combineSets(lhs,last_op,getSetFunc(t))
                else:
                    #print("%s%s:Setting empty left hand side to result of: %s" % (indent_str,name_pref,t))
                    lhs=getSetFunc(t)
                continue
            else:
                #token is an operator, determine next action
                if t in sub_expression_ops:
                    #token is part of a sub expression, look up its details
                    s_expr=self._getSubExprDetail(t)
                    s_expr_start=s_expr[0]
                    s_expr_end=s_expr[1]
                    s_expr_func=s_expr[2]
                    s_expr_allname=s_expr[4]
                    s_expr_name=s_expr[4]
                    #Check if we are currently withing a sub expression:
                    if subExprName:
                        s_expr_end=cur_s_expr[1]
                    if t == s_expr_start:
                        #We are at the start of a new sub expression, so recurse appropriately
                        #print("%s%s:Recursing on subexpression: %s=%s" % (indent_str,name_pref,s_expr_name,t))
                        rec_result=self._evalExpression(tokens,wrap_grouper=False,subExprName=s_expr_name,recurse_lvl=recurse_lvl+1)
                        tokens=rec_result[1]
                        if not lhs:
                            #print("%s%s:Setting empty left hand side to: %s" % (indent_str,name_pref,rec_result[0]))
                            lhs=rec_result[0]
                        elif last_op:
                            #print("%s%s:Combining left hand side. op=%s, rec_result=%s" % (indent_str,name_pref,last_op,rec_result[0]))
                            lhs=self._combineSets(lhs,last_op,rec_result[0])
                            last_op=''
                        else:
                            raise RuntimeError("Unknown error after sub expression recursing: cur_tokens %s lhs: %s last_op: %s" % (''.join(tokens),str(lhs),last_op))
                    if t == s_expr_end:
                        #Next Operator is the ending of the sub expression
                        #print("%s%s:Exiting Recursion on subexpression: %s=%s" % (indent_str,name_pref,s_expr_name,t))
                        return (lhs,tokens)
                elif t == self.operators['group_start_char']:
                    #We are at the start of a grouping, begin recursing
                    #print("%s%s:Recursing on Group operator: %s" % (indent_str,name_pref,t))
                    rec_result=self._evalExpression(tokens,wrap_grouper=False,subExprName=subExprName,recurse_lvl=recurse_lvl+1)
                    tokens=rec_result[1]
                    if not lhs:
                        #print("%s%s:Setting empty left hand side to: %s" % (indent_str,name_pref,rec_result[0]))
                        lhs=rec_result[0]
                    elif last_op:
                        #print("%s%s:Combining left hand side. op=%s, rec_result=%s" % (indent_str,name_pref,last_op,rec_result[0]))
                        lhs=self._combineSets(lhs,last_op,rec_result[0])
                        last_op=''
                    else:
                        raise RuntimeError("Unknown error after group recursing: cur_tokens %s lhs: %s last_op: %s" % (''.join(tokens),str(lhs),last_op))
                elif t == self.operators['group_end_char']:
                    #Next token is the ending of a group
                    #print("%s%s:Exiting recursion on Group operator: %s" % (indent_str,name_pref,t))
                    return(lhs,tokens)
                else:
                    #Token is a verb operator
                    last_op=t
                    continue
        return (lhs,tokens)
    def extractNames(self,expression,wrap_grouper=True,subexpr=None,recurse_leaf=False):
        """
        Take an expression and extract all the nouns out of it

        Args:
            expression      String or List with the expression to extract nouns
                            from

        Returns:
            List where each element is a noun
        """
        nouns={}
        ops=self._allOps()
        subexp_ops=self._subExprOps()
        sub_expr_detail=None
        #Convert expression from string to token List if passed as a String
        if isinstance(expression,str):
            tokens=self._tokenizer(expression)
        else:
            #Assume a List was passed
            tokens=expression
        if not recurse_leaf:
            cur_name='def'
            nouns[cur_name]=[]
        if subexpr:
            sub_expr_detail=self._getSubExprDetail(subexpr)
            cur_name=sub_expr_detail[4]
            nouns[cur_name]=[]
        if wrap_grouper:
            tokens=self._notWrapGrouper(tokens)[0]
        while tokens:
            t=tokens.pop(0)
            if t not in ops:
                nouns[cur_name].append(t)
            else:
                if t not in subexp_ops:
                    continue
                else:
                    if subexpr:
                        #We are inside a subexpr check if we are at the end of our recursion
                        if t == sub_expr_detail[1]: #second elem is the end char
                            #End of expression, return
                            return (nouns,tokens)
                    #Must be at a new subexpression, recurse
                    results=self.extractNames(tokens,wrap_grouper=False,subexpr=t,recurse_leaf=True)
                    #Add in the found noun to our master list
                    for kn in results[0].keys():
                        try:
                            nouns[kn]+=results[0][kn]
                        except KeyError:
                            nouns[kn]=[]
                            nouns[kn]+=results[0][kn]
                    tokens=results[1]
        return nouns
    def getSet(self,name):
        """
        Returns a Set with the give name as the argument

        Args:
            name    Name that gets translated into a set, the expression uses
        """
        raise NotImplementedError


class BaseConditionalExpression(BaseExpression):
    """
    This is a base class for others to inherit from for performing
    conditional expressions
    """
    def _combineVals(self,left,op,right):
        """
        Takes two Bool and combine with either an or,and, or not operator

        Args:
            left    First Bool to be combined with second Bool
            op      String of the Operator to be used to combine the two Bools
            right   Second Bool to be combined with First Bool

        Returns:
            Bool that is the result combining the two values.
        """
        self.logger.debug("_combineVals opts: {} {} {}".format(left,op,right))
        if op in self.operators['and_operators']:
            result=left and right
        elif op in self.operators['or_operators']:
            result=left or right
        elif op in self.operators['not_operators']:
            result=left != right
        else:
            raise ValueError("Unknown operator: {}".format(op))
        self.logger.debug("_combineVals returning: {}".format(result))
        return result
    def _evalExpression(self,expression,subExprName=None,recurse_lvl=0):
        """
        Evaluate an expression and pass to _combineVals etc...
        This does all of the heavy lifting and parsing etc...

        Args:
            expresssion     String or List representing the expression to process
            subExprName     String that is the 'name' of the subexpression
                            to use for getVal function. Mostly used internally
                            when recursing
            recurse_lvl     This indicates the depth of the recusion. Only used
                            internally.

        Returns:
            Tuple, first element is the resulting Bool object, second element is
            a String of any remaning bits of an expression that needs to be
            processed (only used when recursing because of group operators)
        """
        sub_expression_ops=self._subExprOps()
        ops=self._allOps()
        indent_str=self._indent_lvl(recurse_lvl)
        #Convert expression from string to token List if passed as a String
        if isinstance(expression,str):
            tokens=self._tokenizer(expression)
        else:
            #Assume a List was passed
            tokens=expression
        lhs=None
        last_op=''
        #Load up subexpression information within recursion
        if subExprName:
            cur_s_expr=self._getSubExprDetail(name=subExprName)
            getValFunc=cur_s_expr[2]
            name_pref=subExprName
        else:
            getValFunc=self.getVal
            name_pref='Base'
        #self.logger.debug("{}{}:tokens={}".format(indent_str,name_pref,tokens))
        #Loop through all our items
        while tokens:
            t=tokens.pop(0)
            if t not in ops:
                #token is a name/noun, so get the value, and combine if needed
                if last_op:
                    self.logger.debug("{}{}:Combining left hand side. lhs={}, op={}, noun={}".format(indent_str,name_pref,lhs,last_op,t))
                    lhs=self._combineVals(lhs,last_op,getValFunc(t))
                else:
                    self.logger.debug("{}{}:Setting empty left hand side to result of: {}".format(indent_str,name_pref,t))
                    lhs=getValFunc(t)
                continue
            else:
                #token is an operator, determine next action
                if t in sub_expression_ops:
                    #token is part of a sub expression, look up its details
                    s_expr=self._getSubExprDetail(t)
                    s_expr_start=s_expr[0]
                    s_expr_end=s_expr[1]
                    s_expr_func=s_expr[2]
                    s_expr_allname=s_expr[4]
                    s_expr_name=s_expr[4]
                    #Check if we are currently withing a sub expression:
                    if subExprName:
                        s_expr_end=cur_s_expr[1]
                    if t == s_expr_start:
                        #We are at the start of a new sub expression, so recurse appropriately
                        self.logger.debug("{}{}: Recursing on subexpression: {}={}".format(indent_str,name_pref,s_expr_name,t))
                        rec_result=self._evalExpression(tokens,subExprName=s_expr_name,recurse_lvl=recurse_lvl+1)
                        tokens=rec_result[1]
                        if not lhs:
                            self.logger.debug("{}{}: Setting empty left hand side to: {}".format(indent_str,name_pref,rec_result[0]))
                            lhs=rec_result[0]
                        elif last_op:
                            self.logger.debug("{}{}: Combining left hand side. op={}, rec_result={}".format(indent_str,name_pref,last_op,rec_result[0]))
                            lhs=self._combineVals(lhs,last_op,rec_result[0])
                            last_op=None
                        else:
                            raise RuntimeError("Unknown error after sub expression recursing: cur_tokens {} lhs: {} last_op: {}".format(tokens,lhs,last_op))
                    if t == s_expr_end:
                        #Next Operator is the ending of the sub expression
                        self.logger.debug("{}{}: Exiting Recursion on subexpression: {}={}".format(indent_str,name_pref,s_expr_name,t))
                        return (lhs,tokens)
                elif t == self.operators['group_start_char']:
                    #We are at the start of a grouping, begin recursing
                    self.logger.debug("{}{}: Recursing on Group operator: {}".format(indent_str,name_pref,t))
                    rec_result=self._evalExpression(tokens,subExprName=subExprName,recurse_lvl=recurse_lvl+1)
                    tokens=rec_result[1]
                    if not lhs:
                        self.logger.debug("{}{}:Setting empty left hand side to: {}".format(indent_str,name_pref,rec_result[0]))
                        lhs=rec_result[0]
                    elif last_op:
                        self.logger.debug("{}{}:Combining left hand side. op={}, rec_result={}".format(indent_str,name_pref,last_op,rec_result[0]))
                        lhs=self._combineVals(lhs,last_op,rec_result[0])
                        last_op=None
                    else:
                        raise RuntimeError("Unknown error after group recursing: cur_tokens {} lhs: {} last_op: {}".format(tokens,lhs,last_op))
                elif t == self.operators['group_end_char']:
                    #Next token is the ending of a group
                    self.logger.debug("{}{}: Exiting recursion on Group operator: {}".format(indent_str,name_pref,t))
                    return(lhs,tokens)
                else:
                    #Token is a verb operator
                    last_op=t
                    continue
        return (lhs,tokens)
    def processExpression(self,expression):
        """
        This uses _evalExpression to return the resulting Set. This is the
        primary function that should be used.

        Args:
            expression      String representing an expression to process

        Returns:
            Set from the results of processing.
        """
        result=self._evalExpression(expression)
        return result[0]
    def getVal(self,name):
        """
        Returns a Set with the give name as the argument

        Args:
            name    Name that gets translated into a set, the expression uses
        """
        raise NotImplementedError
