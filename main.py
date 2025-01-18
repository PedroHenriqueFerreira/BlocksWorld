from pysat.solvers import Glucose4
from time import time

import sys
from instance_manager.satplan_instance import SatPlanInstance, SatPlanInstanceMapper

from ui import display

def create_literal_for_level(level, literal):
    pure_atom = literal.replace("~", "")
    return f"~{level}_{pure_atom}" if literal[0] == "~" else f"{level}_{pure_atom}"


def create_literals_for_level_from_list(level, literals):
    return [create_literal_for_level(level, literal) for literal in literals]


def create_state_from_true_atoms(true_atoms, all_atoms):
    initial_state = [
        f"~{atom}" for atom in all_atoms if atom not in true_atoms]
    return true_atoms + initial_state


def create_state_from_literals(literals, all_atoms):
    positive_literals = [literal for literal in literals if literal[0] != "~"]
    return create_state_from_true_atoms(positive_literals, all_atoms)


if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("Usage: python your_script.py <filename>")
        sys.exit(1)

    # Inicia timer
    
    timer = time()

    # Instancia o problema, o mapeador de literais e o solver

    satPlanInstance = SatPlanInstance(sys.argv[1])
    instanceMapper = SatPlanInstanceMapper()
    solver = Glucose4()

    # Adiciona os literais verdadeiros do estado inicial

    initial_state = satPlanInstance.get_initial_state()
    initial_state_0 = create_literals_for_level_from_list(0, initial_state)

    instanceMapper.add_list_of_literals_to_mapping(initial_state_0)

    initial_state_0_int = instanceMapper.get_list_of_literals_from_mapping(initial_state_0)

    for literal in initial_state_0_int:
        solver.add_clause([literal])

    # Adiciona os literais falsos do estado inicial

    state_atoms = satPlanInstance.get_state_atoms()

    for atom in state_atoms:
        if atom in initial_state:
            continue

        atom_0 = create_literal_for_level(0, atom)

        instanceMapper.add_literal_to_mapping(atom_0)

        atom_0_int = instanceMapper.get_literal_from_mapping(atom_0)

        solver.add_clause([-atom_0_int])

    actions = satPlanInstance.get_actions()

    t = 0

    print('TRYING TO SOLVE THE PROBLEM...\n')

    while True:
        # Adiciona os literais das ações

        actions_t = create_literals_for_level_from_list(t, actions)

        instanceMapper.add_list_of_literals_to_mapping(actions_t)

        actions_t_int = instanceMapper.get_list_of_literals_from_mapping(actions_t)

        solver.add_clause(actions_t_int)

        # Torna os estados mutuamente exclusivos (opcional)

        for i, atom in enumerate(state_atoms):
            for atom_2 in state_atoms[i + 1:]:
                should_continue = True
                
                # Se o objeto está limpo, então não possui nenhum objeto sobre ele
                
                if (
                    atom.startswith('clear') and 
                    atom_2.startswith('on_') and 
                    atom_2.endswith(atom.split('_')[1])
                ):
                    should_continue = False

                # Se a garra está vazia ou segurando um objeto, então não está segurando quaisquer outros objetos

                if (
                    (
                        atom.startswith('holding') or 
                        atom.startswith('handempty')
                    ) and 
                    atom_2.startswith('holding')
                ):
                    should_continue = False

                # Se a garra está segurando um objeto, então este objeto não está sobre nenhum outro e nem possui nenhum sobre ele

                if (
                    atom.startswith('holding') and
                    atom_2.startswith('on_') and
                    (
                        atom.endswith(atom_2.split('_')[1]) or 
                        atom.endswith(atom_2.split('_')[2])
                    )
                ):
                    should_continue = False
                
                # Se a garra está segurando um objeto, então este objeto não está sobre a mesa  
                
                if (
                    atom.startswith('holding') and
                    atom_2.startswith('ontable') and
                    atom.endswith(atom_2.split('_')[1])
                ):
                    should_continue = False
                
                # Se um objeto está sobre outro, então este objeto não está sobre nenhum outro
                # Se um objeto possui outro sobre ele, então este objeto não possui nenhum outro sobre ele
                
                if (
                    atom.startswith('on_') and 
                    atom_2.startswith('on_') and 
                    (
                        atom.split('_')[1] == atom_2.split('_')[1] or 
                        atom.split('_')[2] == atom_2.split('_')[2]
                    )
                ):
                    should_continue = False

                # Se um objeto está sobre a mesa, então este objeto não está sobre nenhum outro

                if (
                    atom.startswith('on_') and 
                    atom_2.startswith('ontable') and 
                    atom_2.endswith(atom.split('_')[1])
                ):
                    should_continue = False
                
                if should_continue:
                    continue
                
                atom_t = create_literal_for_level(t, atom)
                atom_2_t = create_literal_for_level(t, atom_2)

                instanceMapper.add_literal_to_mapping(atom_t)
                instanceMapper.add_literal_to_mapping(atom_2_t)

                atom_t_int = instanceMapper.get_literal_from_mapping(atom_t)
                atom_2_t_int = instanceMapper.get_literal_from_mapping(atom_2_t)
                
                solver.add_clause([-atom_t_int, -atom_2_t_int])

        for i, (action, action_t_int) in enumerate(zip(actions, actions_t_int)):

            # Torna as ações mutuamente exclusivas

            for action_t_int_2 in actions_t_int[i + 1:]:
                solver.add_clause([-action_t_int, -action_t_int_2])

            # Adiciona os literais das pré-condições

            preconditions = satPlanInstance.get_action_preconditions(action)
            preconditions_t = create_literals_for_level_from_list(t, preconditions)

            instanceMapper.add_list_of_literals_to_mapping(preconditions_t)

            preconditions_t_int = instanceMapper.get_list_of_literals_from_mapping(preconditions_t)

            for literal in preconditions_t_int:
                solver.add_clause([-action_t_int, literal])

            # Adiciona os literais das pós-condições

            posconditions = satPlanInstance.get_action_posconditions(action)
            posconditions_t_plus_1 = create_literals_for_level_from_list(t + 1, posconditions)

            instanceMapper.add_list_of_literals_to_mapping(posconditions_t_plus_1)

            posconditions_t_plus_1_int = instanceMapper.get_list_of_literals_from_mapping(posconditions_t_plus_1)

            for literal in posconditions_t_plus_1_int:
                solver.add_clause([-action_t_int, literal])

            # Adiciona a persistência dos literais de estado

            for atom in state_atoms:
                if atom in posconditions or f'~{atom}' in posconditions:
                    continue

                atom_t = create_literal_for_level(t, atom)
                atom_t_plus_1 = create_literal_for_level(t + 1, atom)

                instanceMapper.add_literal_to_mapping(atom_t)
                instanceMapper.add_literal_to_mapping(atom_t_plus_1)

                atom_t_int = instanceMapper.get_literal_from_mapping(atom_t)
                atom_t_plus_1_int = instanceMapper.get_literal_from_mapping(atom_t_plus_1)

                solver.add_clause([-action_t_int, -atom_t_int, atom_t_plus_1_int])
                solver.add_clause([-action_t_int, atom_t_int, -atom_t_plus_1_int])

        # Adiciona os literais do estado final

        final_state=satPlanInstance.get_final_state()
        final_state_t_plus_1=create_literals_for_level_from_list(t + 1, final_state)

        instanceMapper.add_list_of_literals_to_mapping(final_state_t_plus_1)

        final_state_t_plus_1_int=instanceMapper.get_list_of_literals_from_mapping(final_state_t_plus_1)

        # Imprime o progresso
        
        steps = str(t + 1).rjust(4)
        clauses = str(f'{solver.nof_clauses():,}').rjust(12)
        literals = str(f'{solver.nof_vars():,}').rjust(8)
        time_spent = str(f'{time() - timer:,.2f}').rjust(8)
        
        print(f'STEPS: {steps} | CLAUSES: {clauses} | LITERALS: {literals} | TIME SPENT: {time_spent}s')

        # Resolve o problema

        solver.solve(assumptions=final_state_t_plus_1_int)

        model=solver.get_model()

        if model is None:
            t += 1
            continue

        # Imprime a solução

        print(f'\nPROBLEM SOLVED!\n')

        print(f'SOLUTION STEPS: \n\t{t + 1}')

        print(f'TIME: \n\t{time() - timer:,.2f}s')

        print(f'CLAUSES: \n\t{solver.nof_clauses():,}')

        print(f'LITERALS: \n\t{solver.nof_vars():,}')

        print(f'ACTIONS:')

        literals=instanceMapper.get_list_of_literals_from_mapping_reverse(model)

        steps = []
        
        for literal in literals:
            if literal[0] == '~':
                continue

            for action in actions:
                if action in literal:
                    print(f'\t{literal}')
                    
                    steps.append(literal)
                    
                    break

        break

    display(sys.argv[1], initial_state, steps)
