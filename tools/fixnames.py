# Converts defword/defalt name arguments written as <...> (with ! escapes)
# to the ^~...~ form.  Usage: python3 tools/fixnames.py file.mar...
import re, sys
for p in sys.argv[1:]:
    out = []
    for line in open(p):
        m = re.match(r'(\s*def(?:word|alt)\s+\w+,)<(.*?)>(\s*(?:,.*)?)$', line.rstrip('\n'))
        if m and not line.lstrip().startswith(';'):
            # find the real closing '>' : the name ends at the last '>' not escaped by '!'
            body = line.rstrip('\n')[len(m.group(1))+1:]
            i = 0; name = ''
            while i < len(body):
                c = body[i]
                if c == '!' and i+1 < len(body):
                    name += body[i+1]; i += 2; continue
                if c == '>':
                    break
                name += c; i += 1
            rest = body[i+1:]
            line = m.group(1) + '^~' + name + '~' + rest + '\n'
        out.append(line)
    open(p, 'w').write(''.join(out))
