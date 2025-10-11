import re
import subprocess
import pandas as pd
import numpy as np
import simple_ddl_parser as ddl

# This module requires `mdptools` to be installed in your $PATH

def __strip_quotes(obj):
    if isinstance(obj, str):
        return obj.removeprefix('"').removesuffix('"')
    elif isinstance(obj, dict):
        return {__strip_quotes(k): __strip_quotes(v) for k,v in obj.items()}
    elif isinstance(obj, list):
        return [__strip_quotes(v) for v in obj]
    else:
        return obj

def __clean_columns(columns):
    def __popper(c, n):
        v = c.pop(n)
        return (v, c)
    return dict(__popper(c, 'name') for c in columns)

def mdb_schema(mdb_file, encoding='utf8'):
    sql_schema = subprocess.check_output(['mdb-schema', mdb_file]).decode(encoding)
    # DDLParser doesn't quite like the fact that names are surrounded in [*], so we change these to quotes before parsing.
    sql_schema = sql_schema.replace('[', '"').replace(']', '"')
    parsed = ddl.DDLParser(sql_schema).run(group_by_type=True)['tables']

    return __strip_quotes({t['table_name']: __clean_columns(t['columns']) for t in parsed})


def list_tables(mdb_file, encoding='utf8'):
    return mdb_schema(mdb_file, encoding).keys()


def panda_schema(mdbSchema):
    def __to_numpy_type(t):
        tp = t.get('type', 'Unknown').lower()
        if tp.startswith('double'):
            return np.float_
        elif tp.startswith('long') or (tp.startswith('numeric') and t['size'][1] == 0):
            return np.int_
        elif tp.startswith('text'):
            return np.str_
        else:
            return np.str_
    return {k: __to_numpy_type(v) for k,v in mdbSchema.items()}


def read_table(mdb_file, table_name, *args, **kwargs):
    encoding = kwargs.pop('encoding', 'utf8')
    mdbSchema = mdb_schema(mdb_file, encoding)
    schemas = panda_schema(mdbSchema)
    dtypes = schemas[table_name]
    if dtypes != {}:
        kwargs['dtype'] = dtypes

    proc = subprocess.Popen(['mdb-export', mdb_file, table_name], stdout=subprocess.PIPE)
    return pd.read_csv(proc.stdout, *args, **kwargs)
