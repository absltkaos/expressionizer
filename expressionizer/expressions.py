from .base import BaseConditionalExpression
import logging
import re

class FlatDictExpression(BaseConditionalExpression):
    """
    Extends BaseConditionalExpression to check values in
    a flattened or single level dictionary.

    For example:
    Given a flattened dictionary of:
        {
            'key1.subkey2': 'bob',
            'key1.subkey3': 'carole',
            'key2.foo': 'bar',
            'key2.foo.version': '0.0.4',
            'key2.foo.enabled': True
        }
    The expression: "key1.subkey2=bob" would result in True.

    There is also support for value checking. So with the same example diction above,
    the expression: key2.foo.version>=0.0.4 would result in True

    The expression: "key1.subkey2=bob&&key2.foo.enabled: would return True
    Args:
        flat_dict          A dictionary object that has been flattend
    """
    ops=[ '>=','<=','>','<','!=','=','/','~' ]

    def __init__(self,flat_dict,logger=None):
        self.logger = logger or logging.getLogger(self.__class__.__name__)
        self.operators={
            'group_start_char': '(',
            'group_end_char': ')',
            'not_operators': ['!'],
            'and_operators': ['&',],
            'or_operators': ['|'],
            'sub_expressions': {},
        }
        self.flat_dict=flat_dict
        self.all_name='all'
    def _op_split(self,search):
        """
        Takes a flat dictionary search name and splits it into 3 elements:
            1) Name
            2) Operator
            3) Value

        Args:
            search      String with the search name expression

        Returns:
            Tuple where first element is dict key name, second is operator, and
            third is the value. If no operator is found elements 2 and 3 are None
        """
        op_found=False
        left=search
        o=None
        right=None
        for op in self.ops:
            if op in search:
                op_found=True
                s_split=search.split(op)
                left=s_split[0]
                o=op
                right=s_split[1]
                break
        return (left, o, right)
    def compare_val(self,left_side,op,right_side):
        """
        Compares two value strings together.

        Args:
            left        String left hand value
            op          String with the operators to use for comparing
            right       String right hand value

        Returns:
            Bool    True or False
        """
        def human_keys(astr):
            """
            Sorts keys based on human order.. IE 1 is less than 10 etc..

            alist.sort(key=human_keys) sorts in human order
            """
            keys=[]
            for elt in re.split('(\d+)', astr):
                elt=elt.swapcase()
                try: elt=int(elt)
                except ValueError: pass
                keys.append(elt)
            return keys
        lh=left_side
        rh=right_side
        sv=sorted([lh,rh],key=human_keys)
        ret=False
        if op == '=':
            if lh == rh:
                ret=True
        elif op == '!=':
            if lh != rh:
                ret=True
        elif op == '<':
            if lh != rh and lh == sv[0]:
                ret=True
        elif op == '<=':
            if lh == rh or lh == sv[0]:
                ret=True
        elif op == '>':
            if lh != rh and rh == sv[0]:
                ret=True
        elif op == '>=':
            if lh == rh or rh == sv[0]:
                ret=True
        elif op == '/':
            if rh in lh:
                ret=True
        elif op == '~':
            if re.match(rh,lh):
                ret=True
        else:
          raise ValueError('Unknown operator: %s' %(op))
        self.logger.debug("compare_val: lhs={} op={} rhs={} . Result={}".format(lh,op,rh,ret))
        return ret
    def getVal(self,name):
        """
        Looks 'name' in the flattened dict, performs and performs any comparisons

        Args:
            name        String, representing a key in the flat dict optional operator
                        for comparisons.

        Returns:
            Bool

        Examples of name:
            key2.foo.enabled        Would assume the value of the key is a Boolean and return as such
            key2.foo.version>=0.0.1 Would return true if key2.foo.version is greater than or equal to 0.0.1

        """
        op_data=self._op_split(name)
        kname=op_data[0]
        kop=op_data[1]
        kval=op_data[2]
        result=False
        #See if the key exists in the flat dict
        try:
            value = self.flat_dict[kname]
        except KeyError:
            return result

        #See if we need to do a comparison
        if kop:
            #Perform the comparison
            if self.compare_val(value,kop,kval):
                result=True
        else:
            #No comparison passed see if the value is a bool
            if isinstance(value,bool):
                if value:
                    result=True
        return result

