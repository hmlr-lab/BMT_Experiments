import re
import janus_swi as janus


def split_prolog_args(s):
    args, cur, depth = [], "", 0

    for ch in s:
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1

        if ch == "," and depth == 0:
            args.append(cur.strip())
            cur = ""
        else:
            cur += ch

    if cur.strip():
        args.append(cur.strip())

    return args


def extract_pred_args(literal):
    literal = literal.strip().rstrip(".")
    m = re.match(r"([a-zA-Z_][a-zA-Z0-9_]*)\((.*)\)$", literal)

    if not m:
        return None, []

    return m.group(1), split_prolog_args(m.group(2))


def queries_from_modeb_declarations(mode_declarations):
    queries = []

    for m in mode_declarations:
        m = m.strip().rstrip(".")

        if not m.startswith("modeb"):
            continue

        inside = m[m.find("(") + 1:m.rfind(")")]
        parts = split_prolog_args(inside)

        if len(parts) >= 2:
            q = parts[1].strip()
            if q not in queries:
                queries.append(q)

    return queries


def normalize_agent_names(literal):
    literal = re.sub(r"\bagent[^,\)]*", "A", literal)
    literal = re.sub(r"\bcruiseliner[^,\)]*", "B", literal)
    return literal


def get_example_binding(example):
    _, args = extract_pred_args(example)

    if len(args) < 2:
        raise ValueError(f"Cannot extract A,B from example: {example}")

    return {
        "A": args[0],
        "B": args[1]
    }


def ground_bottom_literal(literal, binding):
    pred, args = extract_pred_args(literal)

    if pred is None:
        return None

    grounded_args = [binding.get(a, a) for a in args]

    return f"{pred}({','.join(grounded_args)})."


def bind_query_with_example(query, binding):
    """
    applies(A,B,R)
    -> applies(agent_1_1,cruiseliner_1_1,R)

    tcpa_closing(A,B)
    -> tcpa_closing(agent_1_1,cruiseliner_1_1)
    """

    pred, args = extract_pred_args(query)

    if pred is None:
        return query

    new_args = [binding.get(a, a) for a in args]

    return f"{pred}({','.join(new_args)})"


def subst_to_literal(query, sol):
    pred, args = extract_pred_args(query)

    grounded_args = [str(sol.get(a, a)) for a in args]

    return f"{pred}({','.join(grounded_args)})"


_LOADED_BK_FILES = set()


def consult_bk_once(bk_path, debug=False):
    global _LOADED_BK_FILES

    if bk_path in _LOADED_BK_FILES:
        return

    if debug:
        print("CONSULTING BK ONCE:", bk_path)

    janus.query_once(f"consult('{bk_path}')")
    _LOADED_BK_FILES.add(bk_path)


def assert_bottom_facts(bottom_facts, debug=False):
    for fact in bottom_facts:
        fact = fact.strip().rstrip(".")

        if not fact:
            continue

        query = f"assertz(({fact}))"

        if debug:
            print("ASSERT:", query)

        janus.query_once(query)


def clear_bottom_facts(bottom_facts, debug=False):
    for fact in bottom_facts:
        pred, args = extract_pred_args(fact)

        if pred is None:
            continue

        query = f"retractall({pred}({','.join(['_'] * len(args))}))"

        if debug:
            print("RETRACT:", query)

        janus.query_once(query)


def modify_bcrl_janus_from_bk(
    bk_path,
    bottom_clause_dict,
    mode_declarations,
    normalize=True,
    debug=False
):
    consult_bk_once(bk_path, debug=debug)

    query_literals = queries_from_modeb_declarations(mode_declarations)

    output = {}

    for example, bottom_literals in bottom_clause_dict.items():

        binding = get_example_binding(example)

        bottom_facts = []

        for lit in bottom_literals:
            grounded = ground_bottom_literal(lit, binding)
            if grounded:
                bottom_facts.append(grounded)

        if debug:
            print("\n================================")
            print("Example:", example)
            print("Binding:", binding)
            print("Modeb queries:", query_literals)
            print("Ground bottom facts:")
            for f in bottom_facts:
                print("  ", f)

        assert_bottom_facts(bottom_facts, debug=debug)

        if normalize:
            updated_literals = [
                normalize_agent_names(lit)
                for lit in bottom_literals
            ]
        else:
            updated_literals = list(bottom_literals)

        for q in query_literals:

            grounded_q = bind_query_with_example(q, binding)

            if debug:
                print("\nQUERY:", grounded_q)

            try:
                solutions = list(janus.query(grounded_q))
            except Exception as e:
                print("FAILED QUERY:", grounded_q)
                clear_bottom_facts(bottom_facts, debug=debug)
                raise e

            for sol in solutions:
                lit = subst_to_literal(grounded_q, sol)

                if normalize:
                    lit = normalize_agent_names(lit)

                if lit not in updated_literals:
                    updated_literals.append(lit)

                    if debug:
                        print("  ADDED:", lit)

        clear_bottom_facts(bottom_facts, debug=debug)

        output[example] = updated_literals

    return output