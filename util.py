import re
import PyGol as pygol
from janus_test import *
from bc_pruner import *


mode_declarations = [
    # Heads
    "modeb(*, applies(A,B,R)).",
    "modeb(*, role(A,B,R)).",
    "modeb(*, priority(A,B,R1,R2,W)).",

    # Primitive facts
    "modeb(*, sector(A,B,S)).",
    "modeb(*, range(A,B,R)).",
    "modeb(*, dcpa(A,B,D)).",
    "modeb(*, tcpa(A,B,T)).",
    "modeb(*, bearing(A,B,V)).",
    "modeb(*, distance(A,B,V)).",
    "modeb(*, status(A,S)).",
    "modeb(*, waterway(A,W)).",
    "modeb(*, constraint_draught(A)).",
    "modeb(*, clock(C)).",

    # Geometric abstractions
    "modeb(*, arc_overtaking(A,B)).",
    "modeb(*, port_forward(A,B)).",
    "modeb(*, port_aft(A,B)).",
    "modeb(*, starboard_forward(A,B)).",
    "modeb(*, starboard_aft(A,B)).",
    "modeb(*, port(A,B)).",
    "modeb(*, starboard(A,B)).",
    "modeb(*, forward(A,B)).",
    "modeb(*, aft(A,B)).",

    # Derived concepts
    "modeb(*, dcpa_unsafe(A,B)).",
    "modeb(*, dcpa_safe(A,B)).",
    "modeb(*, tcpa_closing(A,B)).",
    "modeb(*, range_actionable(A,B)).",
    "modeb(*, timeliness(A,B,T)).",
    "modeb(*, risk_collision(A,B)).",
    "modeb(*, close_quarters(A,B)).",
    "modeb(*, close_quarters_developing(A,B)).",

    # Recursive predicates
    "modeb(*, applies(A,B,R)).",
    "modeb(*, applies(A,R)).",
    "modeb(*, role(A,B,R)).",
    "modeb(*, priority(A,B,R1,R2,W))."
]

K = [
 'ahead',
 'port_bow_forward',
 'port_bow_broad',
 'port_beam_forward',
 'port_beam',
 'port_beam_aft',
 'port_quarter_broad',
 'port_quarter_aft',
 'astern',
 'starboard_quarter_aft',
 'starboard_quarter_broad',
 'starboard_beam_aft',
 'starboard_beam',
 'starboard_beam_forward',
 'starboard_bow_broad',
 'starboard_bow_forward',
 "aft", "forward",
 'n', 'nne', 'ne', 'ene', 'e', 'ese', 'se', 'sse', 's', 'ssw', 'sw', 'wsw', 'w', 'wnw', 'nw', 'nnw',
 "very_close",
    "close",
    "middle", "marginal",
    "far",
    "very_far", "safe",
    "short", "long", "medium", "opening", "imminent",  "starboard", "large", "port", "small", "opening"
]


constraints={
        "starboard_forward": ["starboard", "forward",],  
        "port_forward":      ["port", "forward", ],     
        "range_actionable":["range"],
        "applies":["sector", "aft", "forward", "ahead", "forward"],

    }

def return_substring(string):
    pred = string.split("(")[0]

    if pred in ["cpa", "tcpa", "range", "sector", "bearing", "distance", "course", "course_compass"]:
        return string.rsplit(',', 1)[0]

    if pred in ["course_compass"]:
        return string.split(',')[0]

    if pred in ["add_waypoint_seg"]:
        return "add_waypoint_seg"

    if pred in ["add_waypoint"]:
        return "add_waypoint"
    
    if pred in ["add_waypoint_bin"]:
        return "add_waypoint_bin"
 
    
    return None   # explicit


def replace_starting_with(lst, starts_with, new_value):
    return [
        new_value if item.startswith(starts_with) else item
        for item in lst
    ]


def contains_substring(lst, substring):
    return any(substring in item for item in lst)

def ground_facts_log_file(file_path, not_allowed=[]):
    keys = []
    with open(file_path, "r") as f:
        raw = f.read()

    lines = raw.strip().split("\n")
    clock_pattern = r'clock\((\d+)\)'
    dict = {}
    for line in lines:
        line = line.strip().rstrip(".")
        if not line:
            continue

        parts = [p.strip() for p in line.split("),")]
        parts = [p + ("" if p.endswith(")") else ")") for p in parts]
        #print(parts[0])
        key = int(parts[0].split("(")[1].rstrip(")"))
        #print("Processing time:", key)
        if len(dict)==0:
            dict[key] = parts[1:]
        else:
            #print(parts[1:])
            last_key, last_value = list(dict.items())[-1]
            
            for eachi in parts[1:]:
                substring = return_substring(eachi)
                #print(substring)
                if  substring == "add_waypoint" :
                    #print("I am here", substring, parts[0])
                    time = int(re.findall(r"\d+", parts[0])[0])
                    keys.append(time)
                    last_value.append(eachi)
                elif substring is not None:
                    #print("Replacing", substring, "with", eachi)
                    last_value = replace_starting_with(last_value, substring, eachi)



            if contains_substring(last_value, "add_waypoint")  and  not(contains_substring(parts[1:], "add_waypoint")) :
                #print("Removing add_waypoint_seg from last_value")
                lst = [item for item in last_value if not item.startswith(tuple(["add_waypoint"]))]
            
            
                dict[key] = lst
            else:
                dict[key] = last_value


            
           
                
    return dict, keys



def generate_facts_examples(state_list_pos1, keys, ex=1, print_facts=False, skip_prefixes=[]):
    facts_new = []
    positive_examples = []
    positive_examples_1 = []
    for id1, i in enumerate(keys):
        new_agent = f"agent_{ex}_{id1+1}"
        cruiseliner = f"cruiseliner_{ex}_{id1+1}"

        for fact in state_list_pos1.get(i, []):
            #print(fact)
            # Replace ONLY standalone 'agent'
            fact = re.sub(r"\bagent\b", new_agent, fact)
            fact_1 = re.sub(r"\bagent\b", new_agent, fact)

            # Replace ONLY exact 'cruiseliner1'
            fact = re.sub(r"\bcruiseliner1\b", cruiseliner, fact)
            fact_1 = re.sub(r"\bcruiseliner1\b", new_agent, fact_1)


            # # Skip if new_agent appears 2+ times as a token
            # if len(re.findall(rf"\b{re.escape(new_agent)}\b", fact)) >= 2:
            #     positive_examples_1.append(fact)
            #     continue
            
            # Skip if fact starts with any of the skip_prefixes
            if any(p in fact for p in skip_prefixes):
                continue
            #print(fact)
            #print("\t", fact)
            

            if "add_waypoint" in fact: #or "add_waypoint" in fact or "add_waypoint_bin" in fact:
                
                positive_examples.append(fact)
            else:
                facts_new.append(fact)


            
        if print_facts:
            print(f"--- Facts for agent at time {i} ---")
            for fact in state_list_pos1.get(i, []):
                print(fact)
            print("\n")
    return facts_new, positive_examples


def generate_bk_from_log(path, verbose=False):
    facts = []
    examples = []
    for count, eachpath in enumerate(path):
        state_list_pos_1, key_1 = ground_facts_log_file(eachpath)
        facts_new_1, examples_1 = generate_facts_examples(state_list_pos_1, key_1, ex=count+1, print_facts=verbose, skip_prefixes=[])

        facts = facts+facts_new_1
        examples = examples + examples_1
    return facts, examples




def modify_bcrl_1(P1,Col_Reg_Rules, py_function):
    head_literals = []
    P2 ={}
    for i in Col_Reg_Rules:
        head= pygol.Meta(i).head
        if head not in head_literals:
            head_literals.append(head)
    for k,v in P1.items():
        #print("Processing:", k)
        kb_bcrl = pl.KnowledgeBase()
        if py_function:
            for fname, f in py_function.items():
                kb_bcrl.register_py_function(fname, f)
        kb_bcrl.add_clauses(Col_Reg_Rules)
        kb_bcrl.add_clauses(v)

        for j in head_literals:
        
            #print("Querying:", j)

            # Query the knowledge base for the head literal
            results = pl.show_results_1(kb_bcrl.query(j)).sub
            #print("r", results)
            status= pl.show_results_1(kb_bcrl.query(j)).stat
            proof= pl.show_results_1(kb_bcrl.query(j)).proof
            #print("\t",proof)
            
            #v = substitute_rules_with_values(results, proof)
            #print(v)
            if status and results:
                if type(results)==dict:
                    results = [results]
                clause_1=""
                #print(results)
                for eachr in results:
                    #print(eachr)
                    args = []
                    for l in pygol.Clause(j).args():
                        #print(l)
                        
                        if l in eachr.keys():
                            #print(1)
                            #if "Var" in eachr[l]:
                                #print("dany", sub[eachr[l]])
                            if "_" in eachr[l]:
                                val = pygol.Clause(eachr[l]).args()[0]
                                args.append(val.split("_")[0])
                            else:
                                args.append(eachr[l])
                        else:
                            #print(2)
                            args.append(l)
                    #print(len(set(args)), len(args))
                    if len(set(args))==len(args):
                        clause_1 = pygol.generate_clause(pygol.Clause(j).predicate, args)
                    #print("\t",j, clause_1)
                if clause_1:
                    
                    if clause_1 not in P1[k]:
                        P1[k].append(clause_1)
    return P1





def pretty_print_prolog(rule_str):
    head, body = rule_str.split(":-", 1)

    literals = re.split(r',(?![^()]*\))', body.rstrip('.'))

    print(f"{head} :-")
    for i, lit in enumerate(literals):
        lit = lit.strip()
        if i < len(literals) - 1:
            print(f"    {lit},")
        else:
            print(f"    {lit}.")

import janus_swi as janus

def heads_from_mode_declarations(mode_declarations):
    """
    Converts mode declarations into query heads.

    Example:
        modeh(*, applies(+ship,+ship,#rule)).
    becomes:
        applies(X,Y,Rule)
    """

    heads = []

    for m in mode_declarations:
        m = m.strip().rstrip(".")

        if not m.startswith("modeh"):
            continue

        inside = m[m.find("(")+1 : m.rfind(")")]

        # remove recall part before first comma
        _, pred_part = inside.split(",", 1)
        pred_part = pred_part.strip()

        pred = pred_part.split("(")[0]
        args_raw = pred_part[pred_part.find("(")+1 : pred_part.rfind(")")]

        args = []
        var_count = 0

        for a in args_raw.split(","):
            a = a.strip()

            if a.startswith("+") or a.startswith("-"):
                var_count += 1
                args.append(chr(87 + var_count))  # X,Y,Z...

            elif a.startswith("#"):
                const_name = a[1:]
                args.append(const_name.capitalize())

            else:
                var_count += 1
                args.append(chr(87 + var_count))

        head = pygol.generate_clause(pred, args)

        if head not in heads:
            heads.append(head)

    return heads


def _janus_all_solutions(query_literal):
    """
    Query Prolog and return all substitutions as Python dictionaries.
    Example:
        applies(X,Y,rule17a2_standon_may_act)
    returns:
        [{'X': 'a', 'Y': 'b'}, ...]
    """
    q = query_literal.strip().rstrip(".")

    vars_in_query = []
    for v in pygol.Clause(q).args():
        if re.match(r"^[A-Z_]", v):
            vars_in_query.append(v)

    solutions = []

    for sol in janus.query(q):
        one = {}
        for v in vars_in_query:
            if v in sol:
                one[v] = str(sol[v])
        solutions.append(one)

    return solutions

def _clear_dynamic_predicates(clauses):
    """
    Remove predicates loaded for one BCRL example.
    """
    seen = set()

    for c in clauses:
        try:
            head = pygol.Meta(c).head if ":-" in c else c
            pred = pygol.Clause(head).predicate
            arity = len(pygol.Clause(head).args())
            seen.add((pred, arity))
        except Exception:
            pass

    for pred, arity in seen:
        janus.query_once(f"retractall({pred}({','.join(['_'] * arity)}))")

def _consult_clauses_in_janus(clauses):
    """
    Assert Prolog clauses dynamically into SWI-Prolog using Janus.
    """
    for c in clauses:
        c = c.strip()
        if not c:
            continue
        if not c.endswith("."):
            c += "."
        janus.query_once(f"assertz(({c[:-1]}))")

def modify_bcrl_1_janus(P1, Col_Reg_Rules, mode_declarations):
    head_literals = heads_from_mode_declarations(mode_declarations)

    for k, bcrl_literals in P1.items():

        all_loaded_clauses = [
            c for c in (Col_Reg_Rules + bcrl_literals)
            if c is not None and str(c).strip()
        ]

        _consult_clauses_in_janus(all_loaded_clauses)

        for head_query in head_literals:
            results = _janus_all_solutions(head_query)

            if not results:
                continue

            for sub in results:
                args = []

                for arg in pygol.Clause(head_query).args():
                    if arg in sub:
                        val = sub[arg]
                        if "_" in val:
                            val = val.split("_")[0]
                        args.append(val)
                    else:
                        args.append(arg)

                if len(set(args)) != len(args):
                    continue

                grounded_clause = pygol.generate_clause(
                    pygol.Clause(head_query).predicate,
                    args
                )

                if grounded_clause not in P1[k]:
                    P1[k].append(grounded_clause)

        _clear_dynamic_predicates(all_loaded_clauses)

    return P1



def read_modes(file_path, strip_empty=True):
    """
    Read a text file and return a list of lines.

    Parameters
    ----------
    file_path : str
        Path to the text file.
    strip_empty : bool, optional
        If True, remove empty lines and strip whitespace.

    Returns
    -------
    list
        List of lines from the file.
    """
    with open(file_path, "r", encoding="utf-8") as f:
        if strip_empty:
            return [line.strip() for line in f if line.strip()]
        else:
            return [line.rstrip("\n") for line in f]
        


def learn_rules(facts, examples, bk_path):
    Hypothesis = []
    for i, pos in enumerate(examples):
        neg = []
        for j, item in enumerate(examples):
            if i != j:
                neg.append(item)

        P, N = pygol.bottom_clause_generation(file=facts,  
                                        constant_set = K ,  
                                        container = "memory",
                                        positive_example=[pos], 
                                        negative_example=neg,tqdm_disable=True)
        

        P_inter = modify_bcrl_janus_from_bk(
        bk_path=bk_path,
        bottom_clause_dict=P,
        mode_declarations=mode_declarations,
        debug=False
    )
        
        N_inter = modify_bcrl_janus_from_bk(
        bk_path=bk_path,
        bottom_clause_dict=N,
        mode_declarations=mode_declarations,
        debug=False
    )

        P1 = prune_bottom_clauses_from_file(
        bk_file=bk_path,
        bottom_clauses=P_inter,
        verbose=False,  explicit_constraints=  constraints      # set True to see why each literal was removed/kept
        )

        N1 = prune_bottom_clauses_from_file(
        bk_file=bk_path,
        bottom_clauses=N_inter,
        verbose=False,  explicit_constraints=  constraints      # set True to see why each literal was removed/kept
        )

        Train_P = {i:j for i,j in P1.items()}
        Train_N = {i:j for i,j in N1.items()}

        model_1 = pygol.pygol_learn(Train_P, Train_N,  constant_set = K,  max_literals=5,  exact_literals=True, distinct=False, 
                            key_size=len(Train_P), min_pos=1, max_neg = 1, verbose=True)
        
        #print("Learned Hypothesis:", model_1.hypothesis)
        #write a funtcion to print model_1.hypothesis in a readable format like prolog rules
        for i in model_1.hypothesis:
            #pretty_print_prolog(i)
            Hypothesis.append(i)
        #print("-----------------------------")
    return Hypothesis