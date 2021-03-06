from Compiler.Globals import *

"""
This file holds functions that generate general Brainfuck code
And general functions that are not dependent on other objects
"""


# =================
#  Brainfuck code
# =================


def get_readint_code():
    # res, tmp, input, loop
    # tmp is used for multiplication
    """
    res = 0
    loop = 1

    while loop
        loop = 0
        input = input()
        if input != newline # todo add a eof check as well. run it in several interpreters to look for common ways for "end of number" input
            loop = 1
            res *= 10 + char_to_digit(input)
    """

    code = "[-]"  # clear res = 0
    code += ">[-]"  # tmp = 0
    code += ">>[-]+"  # loop = 1

    code += "["  # while loop == 1
    code += "[-]"  # loop = 0
    code += "<"  # point to input
    code += ","  # input character
    code += "----------"  # sub 10 (check for newline)

    code += "["  # if input is not newline
    code += ">"  # point to loop
    code += "+"  # loop = 1

    # multiply res by 10 and add the input digit
    code += "<<<"  # point to res
    code += "[>+<-]"  # move res to tmp
    code += ">"  # point to tmp
    code += "[<++++++++++>-]"  # res = tmp * 10, tmp = 0
    code += ">"  # point to input
    code += "-" * (0x30 - 10)  # convert character to digit by substracting 0x30 from it (we already substracted 10 before)
    code += "[<<+>>-]"  # res += input
    code += "]"  # end if

    code += ">"  # point to loop
    code += "]"  # end while

    code += "<<<"  # point to res

    return code


def get_printint_code():
    # return_cell value_to_print_cell

    code = ">"  # point to value_to_print cell
    code += ">[-]" * 10 + "<" * 10  # zero some cells

    # ==============================================================================================
    # code to print num (taken from https://esolangs.org/wiki/brainfuck_algorithms#Print_value_of_cell_x_as_number_.288-bit.29)
    code += ">>++++++++++<<[->+>-[>+>>]>[+[-<+>]>+>>]<<<<<<]>>[-]>>>++++++++++<[->-[>+>>]>[+[-"
    code += "<+>]>+>>]<<<<<]>[-]>>[>++++++[-<++++++++>]<.<<+>+>[-]]<[<[->-<]++++++[->++++++++"
    code += "<]>.[-]]<<++++++[-<++++++++>]<.[-]<<[-<+>]<"
    # todo either document this or write one of my own
    # ==============================================================================================

    code += "<"  # point to value_to_return cell
    return code


def get_readchar_code():
    # read input into "return value cell". no need to move the pointer
    code = ","
    return code


def get_printchar_code():
    # point to parameter, output it, and then point back to "return value cell"
    code = ">.<"
    return code


def get_set_cell_value_code(new_value, previous_value, zero_next_cell_if_necessary=True):
    # this function returns a code that sets the current cell's value to new_value,
    # given that its previous value is previous_value

    # it may return the "naive" way, of "+"/"-" usage, <offset> times
    # and it may return an optimization using loops, by using the next cell as a loop counter
    # if zero_next_cell_if_necessary is set to False, it assumes that the next cell is already 0

    # after the code of this function is executed, the pointer will point to the original cell
    # this function returns the shorter code between "naive" and "looped"

    offset = new_value - previous_value
    char = "+" if offset > 0 else "-"
    offset = abs(offset)

    # "naive" code is simply +/-, <offset> times
    naive = char * offset

    # "looped" code is "[<a> times perform <b> adds/subs] and then <c> more adds/subs"
    def get_abc(offset):
        # returns a,b,c such that a*b+c=offset and a+b+c is minimal

        min_a, min_b, min_c = offset, 1, 0
        min_sum = min_a + min_b + min_c

        for i in range(1, offset // 2 + 1):
            a, b, c = i, offset // i, offset % i
            curr_sum = a + b + c

            if curr_sum < min_sum:
                min_a, min_b, min_c = a, b, c
                min_sum = curr_sum

        return min_a, min_b, min_c

    a, b, c = get_abc(offset)
    looped = ">"  # point to next cell (loop counter)
    if zero_next_cell_if_necessary:
        looped += "[-]"  # zero it if necessary
    looped += "+" * a  # set loop counter
    looped += "[-<" + char * b + ">]"  # sub 1 from counter, perform b actions
    looped += "<"  # point to "character" cell
    looped += char * c  # c more actions

    if len(naive) < len(looped):
        return naive
    else:
        return looped


def get_move_to_offset_code(offset):
    #  returns code that moves value from current pointer to cell at offset <offset> to the left
    #  after this, the pointer points to the original cell, which is now the next available cell

    code = "<" * offset  # point to destination
    code += "[-]"  # zero destination
    code += ">" * offset  # point to source cell
    code += "[" + "<" * offset + "+" + ">" * offset + "-]"  # increase destination, zero source
    # point to next free location (source, which is now zero)

    return code


def get_copy_to_offset_code(offset):
    #  returns code that copies value from current pointer to cell at offset <offset> to the left
    #  after this, the pointer points to the original cell, which remains unchanged

    code = ">"  # point to temp
    code += "[-]"  # zero temp
    code += "<" * (offset + 1)  # point to destination
    code += "[-]"  # zero destination
    code += ">" * offset  # point to source cell
    code += "[>+" + "<" * (offset + 1) + "+" + ">" * offset + "-]"  # increase temp and destination, zero source
    code += ">"  # point to temp
    code += "[<+>-]"  # move temp to original cell
    code += "<"  # point to original cell

    return code


def get_copy_to_variable_code(ids_map_list, ID_token, current_pointer):
    # returns code that copies value from current pointer to cell of the variable ID
    # after this, the pointer points to the original cell, which remains unchanged

    offset = get_offset_to_variable(ids_map_list, ID_token, current_pointer)
    return get_copy_to_offset_code(offset)


def get_move_to_return_value_cell_code(return_value_cell, current_stack_pointer):
    #  returns code that moves value from current pointer to return_value cell
    #  after this, the pointer points to the original cell, which is now the next available cell

    # we need to move it <current_stack_pointer - return_value_cell> cells left
    return get_move_to_offset_code(current_stack_pointer - return_value_cell)


def get_copy_from_variable_code(ids_map_list, ID_token, current_pointer):
    #  returns code that copies value from cell of variable ID to current pointer, and then sets the pointer to the next cell

    offset = get_offset_to_variable(ids_map_list, ID_token, current_pointer)
    code = "[-]"  # res = 0
    code += ">[-]"  # temp (next cell) = 0
    code += "<" * (offset + 1)  # point to destination cell
    code += "[" + ">" * offset + "+>+" + "<" * (offset + 1) + "-]"  # increase res and temp, zero destination
    code += ">" * (offset + 1)  # point to temp
    code += "[" + "<" * (offset + 1) + "+" + ">" * (offset + 1) + "-]"  # copy temp back to destination
    # at this point we point to the next available cell, which is temp, which is now zero

    return code


def get_token_code(ids_map_list, token, current_pointer):
    # generate code that evaluates the token at the current pointer, and sets the pointer to point to the next available cell
    if token.type == Token.NUM:
        value = get_NUM_token_value(token)
        code = "[-]"  # zero current cell
        code += get_set_cell_value_code(value, 0)  # set current cell to the num value
        code += ">"  # point to the next cell

        return code

    elif token.type == Token.CHAR:
        code = "[-]"  # zero current cell
        code += get_set_cell_value_code(ord(token.data), 0)  # set current cell to the char value
        code += ">"  # point to next cell
        return code

    elif token.type == Token.ID:
        code = get_copy_from_variable_code(ids_map_list, token, current_pointer)
        return code

    elif token.type == Token.TRUE:
        code = "[-]"  # zero current cell
        code += "+"  # current cell = 1
        code += ">"  # point to next cell

        return code

    elif token.type == Token.FALSE:
        code = "[-]"  # zero current cell
        code += ">"  # point to next cell

        return code

    raise NotImplementedError


def get_divmod_code():
    # given that the current pointer points to a, and the cell after a contains b,
    # (i.e the cells look like: --> a, b, ?, ?, ?, ?, ...)
    # returns a code that calculates divmod, and the cells look like this:
    # --> 0, b-a%b, a%b, a/b, 0, 0
    # and the pointer points to the first 0 (which is in the same cell as a used to be)
    ADD_DIVISION_BY_ZERO_CHECK = True

    def get_if_equal_to_0_code(inside_if_code, offset_to_temp_cell):
        """
        given a <inside_if_code>, wraps it with an "if (current_cell == 0) {<inside_if_code>}"

        in the process, it zeros the current cell
        additionally, it uses a temp cell
        the argument <offset_to_temp_cell> is the offset from the current cell to the temp cell
        *** note that the temp cell must be AFTER the cells that the <inside_if_code> touches ***

        <inside_if_code> should assume it starts running when pointing to the current cell
        and it should end its run pointing to the same cell
        """

        # temp cell is initialized to 1, and holds a flag of whether or not we should run <inside_if_code> or not
        # if cell to evaluate is not zero, we set this flag to 0

        code = ">" * offset_to_temp_cell  # point to temp
        code += "[-]+"  # temp = 1
        code += "<" * offset_to_temp_cell  # point to cell to compare to 0

        code += "["  # if it is not zero
        code += ">" * offset_to_temp_cell  # point to temp
        code += "-"  # temp = 0
        code += "<" * offset_to_temp_cell  # point to cell
        code += "[-]"  # zero the cell
        code += "]"  # end if

        code += ">" * offset_to_temp_cell  # point to temp cell
        code += "["  # if it is non zero
        code += "<" * offset_to_temp_cell  # point to cell
        code += inside_if_code  # execute desired code
        # at this point we point to the original cell
        code += ">" * offset_to_temp_cell  # point to temp cell
        code += "-"  # temp = 0
        code += "]"  # end if
        code += "<" * offset_to_temp_cell  # point back to original cell

        return code

    code = ""

    if ADD_DIVISION_BY_ZERO_CHECK:
        # create a prefix code: if (b == 0) {print("Error - Division by zero\n");}

        # copy b to temp cell (via another temp cell) and compare that cell to 0. if its 0, execute error print and go to infinite loop

        code += ">>"  # point to empty cell
        code += "[-]>[-]"  # zero 2 temp cells
        code += "<<"  # point to b
        code += "[>+>+<<-]"  # move b to both cells
        code += ">"  # point to first cell
        code += "[<+>-]"  # move first cell back to b
        code += ">"  # point to second cell

        code_inside_if = "[-]>[-]<>++++++[-<+++++++++++>]<+++.>+++++[-<+++++++++>]<..---.+++.>+++++++++[-<--------->]" \
                         "<-.+++++++++++++.-------------.>++++++[-<++++++>]<.>++++++[-<++++++>]<+.+++++++++++++.-----" \
                         "--------.++++++++++.----------.++++++.-.>++++++[-<------------->]<.>++++++[-<+++++++++++>]<" \
                         ".>+++[-<+++++++>]<++.>++++++++[-<----------->]<-.>+++++++++[-<++++++++++>]<.>+++[-<------->" \
                         "]<.+++++++++++++.---.>++++++++++[-<---------->]<-."  # print("Error - Division by zero\n");
        code_inside_if += "[]"  # infinite loop

        code += get_if_equal_to_0_code(code_inside_if, offset_to_temp_cell=1)
        code += "<<<"  # point to a

        # ======================= end of prefix =======================

    # a, b, w, x, y, z

    code += ">>[-]>[-]>[-]>[-]<<<<<"  # zero w,x,y,z, and point to a
    code += "["  # while a != 0

    code += "-"  # decrease a by 1
    code += ">-"  # decrease b by 1
    code += ">+"  # increase w by 1
    code += "<"  # point to b
    code += "[->>>+>+<<<<]>>>>[-<<<<+>>>>]"  # copy b to y (via z)
    code += "<"  # point to y

    code_inside_if = ""
    code_inside_if += "<+"  # increase x by 1
    code_inside_if += "<"  # point to w
    code_inside_if += "[-<+>]"  # copy w to b (b is already 0) (after this we point to w)
    code_inside_if += ">>"  # point to y

    # get_if_equal_to_0 also zeros y
    # i set offset_to_temp_cell = 1 because it can use z, since it is unused inside the if
    code += get_if_equal_to_0_code(inside_if_code=code_inside_if, offset_to_temp_cell=1)

    code += "<<<<"  # point to a
    code += "]"  # end while

    """
    a, b, w, x, y, z


    w, x, y, z = 0, 0, 0, 0

    while a != 0
        a -= 1
        b -= 1
        w += 1

        if b == 0:  (this means that w = original b) (implementation: copy b to y (via z) and compare y to 0, (then zero y))
            x += 1
            b = w
            w = 0




    at the end:
    w = a%b
    x = a/b
    b = b-a%b

    """

    return code


def get_bitwise_code(code_logic):
    # a, b, c, w, x, y, z, bit1, bitcounter, res
    # code_logic uses the cells y, z, and bit1. Where y is res and z and bit1 are the bits.
    # y is zero. z and bit1 should be zero after code_logic.

    code = ">" * 7  # point to bit1
    code += "[-]"  # zero bit1
    code += ">"  # point to bitcounter
    code += ">[-]<"  # zero res

    code += "[-]--------[++++++++"  # while bitcounter != 8:
    code += "<"
    code += "<[-]" * 5  # clear c, w, x, y, z
    code += "++"  # c = 2
    code += "<<"  # point to a

    code += "["  # while a != 0:
    code +=     "-"  # a -= 1
    code +=     ">>-"  # c -= 1
    code +=     "[>+>>+<<<-]>[<+>-]"  # copy c to y (using w)
    code +=     ">>"  # point to y
    code +=     ">>+<<"  # bit1 += 1

    code +=     "-["  # if y != 1:
    code +=         "<+"  # x += 1
    code +=         "<<++"  # c += 2 (c was 0)
    code +=         ">" * 5  # point to bit1
    code +=         "--"  # bit1 -= 2 (bit1 was 2)
    code +=         "<<"  # point to y
    code +=         "+"  # set y to 0
    code +=     "]"  # end if

    code +=     "<<<<<"  # point to a
    code += "]"  # end while

    code += ">>>>[<<<<+>>>>-]"  # move x to a (x is a/2)
    code += "<<[-]++"  # c = 2
    code += "<"  # point to b

    code += "["  # while b != 0:
    code +=     "-"  # b -= 1
    code +=     ">-"  # c -= 1
    code +=     "[>+>>+<<<-]>[<+>-]"  # copy c to y (using w)
    code +=     ">>"  # point to y
    code +=     ">+<"  # z += 1

    code +=     "-["  # if y != 1:
    code +=         ">--<"  # z -= 2 (z was 2)
    code +=         "<+"  # x += 1
    code +=         "<<++"  # c += 2 (c was 0)
    code +=         ">>>"  # point to y
    code +=         "+"  # set y to 0
    code +=     "]"

    code +=     "<<<<"  # point to b
    code += "]"  # end while

    # w is a % 2
    # x is a / 2

    code += ">>>[<<<+>>>-]"  # move x to b

    code += ">>"  # point to z
    code += code_logic  # pointer ends at bit1, z and bit1 should be 0 after code

    code += ">[<+<+>>-]<[>+<-]" # copy bit to z (using bit1)

    # y = y << z
    code += "<"
    code += "["  # while z != 0:
    code += "<"  # point to y
    code += "[<+>-]"  # copy y to x
    code += "<[>++<-]"  # copy x to y * 2
    code += ">>-"  # z -= 1
    code += "]"

    code += "<"  # point to y
    code += "[>>>>+<<<<-]"  # res += y

    code += ">>>"  # point to bitcounter
    code += "-" * 7  # loop if bitcounter != 7

    code += "]"  # end while

    code += ">[<<<<<<<<<+>>>>>>>>>-]"  # move res to a
    code += "<<<<<<<<"  # point to b


    return code


def get_unary_prefix_op_code(token, offset_to_variable=None):
    # returns code that:
    # performs op on operand that is at the current pointer
    # the result is placed in the cell of the operand
    # and the pointer points to the cell right after it (which becomes the next available cell)

    if token.type == Token.NOT:
        # a temp
        code = ">"  # point to temp
        code += "[-]+"  # temp = 1
        code += "<"  # point to a
        code += "["  # if a is non-zero
        code += ">-"  # temp = 0
        code += "<[-]"  # zero a
        code += "]"  # end if

        code += ">"  # point to temp
        code += "["  # if temp is non-zero
        code += "<+"  # a = 1
        code += ">-"  # temp = 0
        code += "]"  # end if

        return code

    elif token.type == Token.INCREMENT:
        #  returns code that copies value from variable's cell at given offset, and adds 1 to both the copied and the original cell
        assert offset_to_variable is not None
        offset = offset_to_variable

        code = "[-]"  # res = 0
        code += ">[-]"  # temp (next pointer) = 0
        code += "<" * (offset + 1)  # point to destination cell
        code += "[" + ">" * offset + "+>+" + "<" * (offset + 1) + "-]"  # increase res and temp, zero destination
        code += ">" * offset  # point to res
        code += "+"  # increase res by 1
        code += ">"  # point to temp
        code += "+"  # increase temp by 1
        code += "[" + "<" * (offset + 1) + "+" + ">" * (offset + 1) + "-]"  # copy temp back to destination
        # at this point we point to the next available cell, which is temp, which is now zero

        return code

    elif token.type == Token.DECREMENT:
        #  returns code that copies value from variable's cell at given offset, and subtracts 1 from both the copied and the original cell
        assert offset_to_variable is not None
        offset = offset_to_variable

        code = "[-]"  # res = 0
        code += ">[-]"  # temp (next pointer) = 0
        code += "<" * (offset + 1)  # point to destination cell
        code += "[" + ">" * offset + "+>+" + "<" * (offset + 1) + "-]"  # increase res and temp, zero destination
        code += ">" * offset  # point to res
        code += "-"  # decrease res by 1
        code += ">"  # point to temp
        code += "-"  # decrease temp by 1
        code += "[" + "<" * (offset + 1) + "+" + ">" * (offset + 1) + "-]"  # copy temp back to destination
        # at this point we point to the next available cell, which is temp, which is now zero

        return code

    elif token.type == Token.UNARY_MULTIPLICATIVE:
        #  returns code that copies value from variable's cell at given offset, modifies both the copied and the original cell depending on the op
        assert offset_to_variable is not None
        offset = offset_to_variable

        code = "[-]"  # res = 0
        code += ">[-]"  # temp (next pointer) = 0
        code += "<" * (offset + 1)  # point to destination cell
        code += "[" + ">" * offset + "+>+" + "<" * (offset + 1) + "-]"  # increase res and temp, zero destination
        code += ">" * offset  # point to res

        if token.data in ["**", "//"]:
            code += ">"  # point to temp (x**, x// keep x the same)
        elif token.data == "%%":
            code += "[-]>[-]"  # put 0 in res and temp, and point to temp
        else:
            raise BFSyntaxError("Unexpected unary prefix %s" % str(token))

        code += "[" + "<" * (offset + 1) + "+" + ">" * (offset + 1) + "-]"  # copy temp back to destination
        # at this point we point to the next available cell, which is temp, which is now zero

        return code

    elif token.type == Token.BITWISE_NOT:
        # a temp
        code = "[>+<-]"  # move a into temp
        code += ">"  # point to temp
        code += "+[<->-]"  # invert temp into a

        return code

    raise NotImplementedError


def get_unary_postfix_op_code(token, offset_to_variable):
    # returns code that:
    # performs op on operand that is at the current pointer
    # the result is placed in the cell of the operand
    # and the pointer points to the cell right after it (which becomes the next available cell)

    if token.type == Token.INCREMENT:
        #  returns code that copies value from variable's cell at given offset, and adds 1 to the original cell
        offset = offset_to_variable

        code = "[-]"  # res = 0
        code += ">[-]"  # temp (next pointer) = 0
        code += "<" * (offset + 1)  # point to destination cell
        code += "[" + ">" * offset + "+>+" + "<" * (offset + 1) + "-]"  # increase res and temp, zero destination
        code += ">" * (offset + 1)  # point to temp
        code += "+"  # increase temp by 1
        code += "[" + "<" * (offset + 1) + "+" + ">" * (offset + 1) + "-]"  # copy temp back to destination
        # at this point we point to the next available cell, which is temp, which is now zero

        return code

    elif token.type == Token.DECREMENT:
        #  returns code that copies value from variable's cell at given offset, and subtracts 1 from the original cell
        offset = offset_to_variable

        code = "[-]"  # res = 0
        code += ">[-]"  # temp (next pointer) = 0
        code += "<" * (offset + 1)  # point to destination cell
        code += "[" + ">" * offset + "+>+" + "<" * (offset + 1) + "-]"  # increase res and temp, zero destination
        code += ">" * (offset + 1)  # point to temp
        code += "-"  # decrease temp by 1
        code += "[" + "<" * (offset + 1) + "+" + ">" * (offset + 1) + "-]"  # copy temp back to destination
        # at this point we point to the next available cell, which is temp, which is now zero

        return code

    elif token.type == Token.UNARY_MULTIPLICATIVE:
        # returns code that copies value from variable's cell at given offset, and modifies the original cell depending on the operation
        offset = offset_to_variable

        code = "[-]"  # res = 0
        code += ">[-]"  # temp (next pointer) = 0
        code += "<" * (offset + 1)  # point to destination cell
        code += "[" + ">" * offset + "+>+" + "<" * (offset + 1) + "-]"  # increase res and temp, zero destination
        code += ">" * (offset + 1)  # point to temp

        if token.data in ["**", "//"]:
            pass  # x**,x// keeps x the same
        elif token.data == "%%":
            code += "[-]"  # x%% modifies x to 0
        else:
            raise BFSyntaxError("Unexpected unary postfix %s" % str(token))

        code += "[" + "<" * (offset + 1) + "+" + ">" * (offset + 1) + "-]"  # copy temp back to destination
        # at this point we point to the next available cell, which is temp, which is now zero

        return code

    raise NotImplementedError


def get_op_between_literals_code(op_token):
    # returns code that:
    # performs op on 2 operands
    # the first operand is at current pointer, and the second operand is at current pointer + 1
    # the code can destroy second operand, and everything after it

    # the result is placed in the cell of the first operand
    # and the pointer points to the cell right after it (which becomes the next available cell)

    op = op_token.data
    if op == "+" or op == "-":
        res = ">[<" + op + ">-]"  # increase/decrease first operand and decrease second operand
        # the pointer points to the next available cell, which is the second operand, which is 0

        return res

    elif op == "*":
        # a, b, temp1, temp2
        res = ">>[-]>[-]"  # put 0 into temp1, temp2
        res += "<<<"  # point to first operand
        res += "[>>>+<<<-]"  # move first operand to temp2
        res += ">>>"  # point to temp2

        # do in a loop: as long as temp2 != 0
        res += "["

        res += "<<"  # point to second operand
        res += "[<+>>+<-]"  # add it to first operand and temp1
        res += ">"  # point to temp1
        res += "[<+>-]"  # move it to second operand

        # end loop
        res += ">"  # point back to temp2
        res += "-"  # decrease temp2
        res += "]"

        res += "<<"  # point back to next available cell (second operand)
        return res

    elif op == "/":
        code = get_divmod_code()
        code += ">>>"  # point to a/b
        code += "[<<<+>>>-]"  # copy a/b to current cell
        code += "<<"  # point to next available cell

        return code

    elif op == "%":
        code = get_divmod_code()
        code += ">>"  # point to a%b
        code += "[<<+>>-]"  # copy a%b to current cell
        code += "<"  # point to next available cell

        return code

    # relops
    elif op == "==":
        # a, b
        res = "[->-<]"  # a = 0, b = b - a
        res += "+"  # a = 1. will hold the result. if a!=b, this is unchanged
        res += ">"  # point to b
        res += "["  # if b == 0, enter the following code
        res += "<->[-]"  # a = 0, b=0
        res += "]"  # end of "loop"

        return res

    elif op == "!=":
        # a, b
        res = "[->-<]"  # a = 0, b = b - a
        # a will hold the result. if a!=b, this is unchanged
        res += ">"  # point to b
        res += "["  # if b == 0, enter the following code
        res += "<+>[-]"  # a = 1, b=0
        res += "]"  # end of "loop"

        return res

    elif op == ">":
        # a, b, c, d

        code = ">>[-]"  # c = 0  (will hold res)
        code += ">[-]"  # d = 0
        code += "<<<"  # point to a

        code += "["  # while a != 0

        code += ">>[-]"  # c = 0
        code += "<"  # point to b
        code += "[>+>+<<-]>[<+>-]"  # copy b to d (via c)
        code += "+"  # c = 1 (will hold res)
        code += ">"  # point to d
        code += "["  # if d != 0
        code += "[-]"  # d = 0
        code += "<-"  # c = 0
        code += "<-"  # b -= 1
        code += ">>"  # point to d
        code += "]"  # end if

        code += "<<<"  # point to a
        code += "-"  # a -= 1

        code += "]"  # end while

        # move c to a
        code += ">>"  # point to c
        code += "[<<+>>-]"  # move c to a
        code += "<"  # point to b (next available cell)

        """
        x > y?


        res = 0
        while x != 0:
            res = 1
            if y != 0:
                res = 0
                y -= 1

            x -= 1
        """

        return code

    elif op == "<":
        # similar to >

        # a, b, c, d

        code = ">>[-]"  # c = 0  (will hold res)
        code += ">[-]"  # d = 0
        code += "<<"  # point to b

        code += "["  # while b != 0

        code += ">[-]"  # c = 0
        code += "<<"  # point to a
        code += "[>>+>+<<<-]>>[<<+>>-]"  # copy a to d (via c)
        code += "+"  # c = 1 (will hold res)
        code += ">"  # point to d
        code += "["  # if d != 0
        code += "[-]"  # d = 0
        code += "<-"  # c = 0
        code += "<<-"  # a -= 1
        code += ">>>"  # point to d
        code += "]"  # end if

        code += "<<"  # point to b
        code += "-"  # b -= 1

        code += "]"  # end while

        # move c to a
        code += "<"  # point to a
        code += "[-]"  # a = 0
        code += ">>"  # point to c
        code += "[<<+>>-]"  # move c to a
        code += "<"  # point to b (next available cell)

        """
        x < y?

        res = 0
        while y != 0:
            res = 1
            if x != 0:
                res = 0
                x -= 1

            y -= 1
        """

        return code

    elif op == "<=":
        # a, b, c, d

        code = ">>[-]+"  # c = 1  (will hold res)
        code += ">[-]"  # d = 0
        code += "<<<"  # point to a

        code += "["  # while a != 0

        code += ">>[-]"  # c = 0
        code += "<"  # point to b
        code += "[>+>+<<-]>[<+>-]"  # copy b to d (via c)
        code += ">"  # point to d
        code += "["  # if d != 0
        code += "[-]"  # d = 0
        code += "<+"  # c = 1
        code += "<-"  # b -= 1
        code += ">>"  # point to d
        code += "]"  # end if

        code += "<<<"  # point to a
        code += "-"  # a -= 1

        code += "]"  # end while

        # move c to a
        code += ">>"  # point to c
        code += "[<<+>>-]"  # move c to a
        code += "<"  # point to b (next available cell)

        """
        x <= y?


        res = 1
        while x != 0:
            res = 0

            if y != 0:
                res = 1
                y -= 1

            x -= 1
        """

        return code

    elif op == ">=":
        # similar to <=

        # a, b, c, d

        code = ">>[-]+"  # c = 1  (will hold res)
        code += ">[-]"  # d = 0
        code += "<<"  # point to b

        code += "["  # while b != 0

        code += ">[-]"  # c = 0
        code += "<<"  # point to a
        code += "[>>+>+<<<-]>>[<<+>>-]"  # copy a to d (via c)
        code += ">"  # point to d
        code += "["  # if d != 0
        code += "[-]"  # d = 0
        code += "<+"  # c = 1
        code += "<<-"  # a -= 1
        code += ">>>"  # point to d
        code += "]"  # end if

        code += "<<"  # point to b
        code += "-"  # b -= 1

        code += "]"  # end while

        # move c to a
        code += "<"  # point to a
        code += "[-]"  # a = 0
        code += ">>"  # point to c
        code += "[<<+>>-]"  # move c to a
        code += "<"  # point to b (next available cell)

        """
        x >= y?


        res = 1
        while y != 0:
            res = 0

            if x != 0:
                res = 1
                x -= 1

            y -= 1
        """

        return code

    elif op_token.type == Token.AND:
        # a, b, temp
        code = ">>[-]"  # zero temp
        code += "<<"  # point to a
        code += "["  # if a is non-zero

        code += ">"  # point to b
        code += "["  # if b is non-zero
        code += ">+"  # temp = 1
        code += "<[-]"  # zero b
        code += "]"  # end if

        code += "<"  # point to a
        code += "[-]"  # zero a
        code += "]"  # end if

        code += ">>"  # point to temp
        code += "["  # if non zero
        code += "<<+"  # a = 1
        code += ">>-"  # temp = 0
        code += "]"  # end if

        code += "<"  # point to b (next available cell)

        return code

    elif op_token.type == Token.OR:
        # a, b, temp
        code = ">>[-]"  # zero temp
        code += "<<"  # point to a
        code += "["  # if a is non-zero

        code += ">"  # point to b
        code += "[-]"  # zero b
        code += ">"  # point to temp
        code += "+"  # temp = 1
        code += "<<"  # point to a
        code += "[-]"  # zero a
        code += "]"  # end if

        code += ">"  # point to b
        code += "["  # if b is non-zero
        code += ">"  # point to temp
        code += "+"  # temp = 1
        code += "<"  # point to b
        code += "[-]"  # zero b
        code += "]"  # end if

        code += ">"  # point to temp
        code += "["  # if temp == 1
        code += "<<+"  # a = 1
        code += ">>"  # point to temp
        code += "-"  # zero temp
        code += "]"  # end if

        code += "<"  # point to b (next available cell)

        return code

    elif op == "<<":
        # a, b, temp

        code = ">>[-]"  # zero temp
        code += "<"  # point to b

        code += "[" # while b != 0
        code += "<" # point to a
        code += "[>>+<<-]" # copy a to temp
        code += ">>" # point to temp
        code += "[<<++>>-]" # multiply temp by 2 and store result in a
        code += "<-" # point to b and b -= 1
        code += "]" # end while

        return code

    elif op == ">>":
        # a, b, c, x, y, z

        code = ">" # point to b
        code += ">[-]" * 4 # clear 4 cells
        code += "<" * 4 # point to b

        code += "[" # while b != 0
        code += ">++" # set c to 2
        code += "<<" # point to a

        code += "[" # while a != 0
        code += "-" # a -= 1
        code += ">>-" # c -= 1
        code += "[>>+>+<<<-]>>>[<<<+>>>-]" # copy c to y (via z)
        code += "<" # point to y

        code += "-[" # if y == 0
        code += "<+" # x += 1
        code += "<++" # set c to 2
        code += ">>"
        code += "+" # zero y
        code += "]" # end if

        code += "<<<<" # point to a
        code += "]" # end while

        code += ">>>" # point to x
        code += "[<<<+>>>-]" # move x to a
        code += "<[-]" # zero c
        code += "<-" # b -= 1
        code += "]" # end while

        return code

    elif op_token.type == Token.BITWISE_AND:
        code = get_bitwise_code("[->[-<<+>>]<]>[-]")

        return code

    elif op_token.type == Token.BITWISE_OR:
        code = get_bitwise_code("[>+<-]>[[-]<<+>>]")

        return code

    elif op_token.type == Token.BITWISE_XOR:
        code = get_bitwise_code("[>-<-]>[[-]<<+>>]")

        return code

    raise NotImplementedError


def get_print_string_code(string):
    code = "[-]"  # zero current cell
    code += ">[-]"  # zero next cell (will be used for loop counts)
    code += "<"  # point to original cell ("character" cell)

    prev_value = 0
    for i in range(len(string)):
        current_value = ord(string[i])

        code += get_set_cell_value_code(current_value, prev_value, zero_next_cell_if_necessary=False)
        code += "."

        prev_value = current_value

    return code


def get_move_right_index_cells_code(current_pointer, node_index):
    # used for arrays
    # returns a code that evaluates the index, then moves the pointer right, <index> amount of cells
    # at the end of execution, the layout is:
    # 0  index next_available_cell (point to next available cell)

    # index, steps_taken_counter
    code = node_index.get_code(current_pointer)  # index
    code += "[-]"  # counter = 0
    code += "<"  # point to index

    code += "["  # while index != 0
    code += ">>"  # point to new_counter (one after current counter)
    code += "[-]"  # zero new_counter
    code += "<"  # move to old counter
    code += "+"  # add 1 to counter
    code += "[>+<-]"  # move old counter to new counter
    code += "<"  # point to old index
    code += "-"  # sub 1 from old index
    code += "[>+<-]"  # move old index to new index
    code += ">"  # point to new index
    code += "]"  # end while

    # old_index=0 new_index res (pointing to old index)
    code += ">>"  # point to res

    return code


def get_move_left_index_cell_code():
    # used for arrays
    # complement of "get_move_right_index_cells_code"
    # assumes the layout is:
    # value, index (pointing to index)
    # moves <index> cells left, and moving <value> along with it
    # in the end, point to one cell after <value> (which becomes the next available cell)

    # layout: res, index (pointing to index)
    code = "["  # while new_index != 0
    code += "<"  # point to res
    code += "[<+>-]"  # move res to the left
    code += ">"  # point to new_index
    code += "-"  # sub 1 from index
    code += "[<+>-]"  # move new_index to left
    code += "<"  # point to new index
    code += "]"  # end while

    # now res is at the desired cell, and we point to the next available cell

    return code


# =================
#     General
# =================

def get_NUM_token_value(token):
    if token.data.startswith("0x"):
        return int(token.data, 16)
    else:
        return int(token.data)


def get_variable_from_ID_token(ids_map_list, ID_token):
    ID = ID_token.data
    # given an id, goes through the ids map list and returns the index of the first ID it finds
    for i in range(len(ids_map_list)):
        ids_map = ids_map_list[i].IDs_dict
        if ID in ids_map:
            return ids_map[ID]
    raise BFSemanticError("'%s' does not exist" % str(ID_token))


def get_variable_dimensions(ids_map_list, ID_token):
    variable = get_variable_from_ID_token(ids_map_list, ID_token)
    return variable.dimensions


def get_id_index(ids_map_list, ID_token):
    variable = get_variable_from_ID_token(ids_map_list, ID_token)
    return variable.cell_index


def get_offset_to_variable(ids_map_list, ID_token, current_pointer):
    offset = current_pointer - get_id_index(ids_map_list, ID_token)
    return offset
