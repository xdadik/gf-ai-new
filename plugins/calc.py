# pyre-ignore-all-errors
import ast  # type: ignore  # pyre-ignore
import operator  # type: ignore  # pyre-ignore
from telegram import Update  # type: ignore  # pyre-ignore
from telegram.ext import CommandHandler, ContextTypes  # type: ignore  # pyre-ignore

PLUGIN_DESCRIPTION = "Calculator using /calc <math expression>"

# Safe evaluation of math expressions
def safe_eval(expr):
    """
    Safely evaluate a mathematical expression using ast.
    Supported operators: +, -, *, /, **, %
    """
    operators = {
        ast.Add: operator.add,
        ast.Sub: operator.sub,
        ast.Mult: operator.mul,
        ast.Div: operator.truediv,
        ast.Pow: operator.pow,
        ast.Mod: operator.mod,
        ast.USub: operator.neg
    }

    def evaluate(node):
        if isinstance(node, ast.Num): # <number>
            return node.n
        elif isinstance(node, ast.BinOp): # <left> <operator> <right>
            return operators[type(node.op)](evaluate(node.left), evaluate(node.right))
        elif isinstance(node, ast.UnaryOp): # <operator> <operand> e.g., -1
            return operators[type(node.op)](evaluate(node.operand))
        else:
            raise TypeError(node)

    try:
        # Parse the expression
        node = ast.parse(expr, mode='eval').body
        return evaluate(node)
    except Exception:
        return "Error: Invalid expression"

async def calc_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Evaluates a math expression."""
    if not context.args:
        await update.message.reply_text("Usage: /calc 2 + 2 * 5")
        return
        
    expr = " ".join(context.args)
    result = safe_eval(expr)
    
    await update.message.reply_text(f"🧮 **Result:**\n`{expr} = {result}`", parse_mode="Markdown")

def setup():
    return [CommandHandler("calc", calc_command)]
