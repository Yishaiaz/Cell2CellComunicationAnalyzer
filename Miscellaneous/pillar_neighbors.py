from Miscellaneous.pillars_mask import *
import random


def get_alive_pillars_in_edges_to_l1_neighbors():
    """
    Mapping the alive pillars in the edges to their level 1 background neighbors
    :return: dictionary mapping the alive pillars to their background neighbors, list of the alive pillars in the edges,
            list of the level one background pillars
    """
    pillar2mask = get_mask_for_each_pillar()
    alive_pillars = get_alive_pillars_lst(pillar2mask)
    all_pillars = pillar2mask.keys()
    background_pillars = [pillar for pillar in all_pillars if
                          pillar not in alive_pillars]
    pillar_to_neighbors = get_pillar_to_neighbors()
    edge_pillars = set()
    back_pillars_level_1 = set()
    edge_pillar_to_back_nbrs_level_1 = {}
    for pillar in all_pillars:
        nbrs = pillar_to_neighbors[pillar]
        if pillar in alive_pillars:
            back_neighbors = []
            for n in nbrs:
                if n in background_pillars:
                    edge_pillars.add(pillar)
                    back_neighbors.append(n)
                    back_pillars_level_1.add(n)
            if len(back_neighbors) > 0:
                edge_pillar_to_back_nbrs_level_1[pillar] = back_neighbors

    return edge_pillar_to_back_nbrs_level_1, list(edge_pillars), list(back_pillars_level_1)


def get_background_level_1_to_level_2():
    """
    Mapping pillar in background from level 1 (neighbors of alive pillars) to their neighbors background pillars in level 2
    :return:
    """
    _, _, back_pillars_level_1 = get_alive_pillars_in_edges_to_l1_neighbors()
    pillar_to_neighbors = get_pillar_to_neighbors()
    pillar2mask = get_mask_for_each_pillar()
    alive_pillars = get_alive_pillars_lst(pillar2mask)
    all_pillars = pillar2mask.keys()
    background_pillars = [pillar for pillar in all_pillars if
                          pillar not in alive_pillars]
    back_pillars_l1_to_l2 = {}
    for pillar_l1 in back_pillars_level_1:
        back_pillars_level_2 = []
        for n in pillar_to_neighbors[pillar_l1]:
            if n in background_pillars and n not in back_pillars_level_1:
                back_pillars_level_2.append(n)
        if len(back_pillars_level_2) > 0:
            back_pillars_l1_to_l2[pillar_l1] = back_pillars_level_2

    return back_pillars_l1_to_l2


def get_pillar_to_neighbors():
    """
    Mapping each pillar to its neighbors
    :return:
    """
    last_img = get_last_image(last_image_path)
    alive_centers = get_alive_centers(last_img)
    centers_lst, rule_jump_1, rule_jump_2 = generate_centers_and_rules_from_alive_centers(alive_centers, len(last_img))
    pillar_to_neighbors = {}
    for p in centers_lst:
        neighbors_lst = set()

        n1 = (p[0] - rule_jump_1[0], p[1] - rule_jump_1[1])
        if n1 in centers_lst:
            neighbors_lst.add(n1)

        n2 = (p[0] + rule_jump_1[0], p[1] + rule_jump_1[1])
        if n2 in centers_lst:
            neighbors_lst.add(n2)

        n3 = (p[0] - rule_jump_2[0], p[1] - rule_jump_2[1])
        if n3 in centers_lst:
            neighbors_lst.add(n3)

        n4 = (p[0] + rule_jump_2[0], p[1] + rule_jump_2[1])
        if n4 in centers_lst:
            neighbors_lst.add(n4)

        n_minus1_minus2 = (n1[0] - rule_jump_2[0], n1[1] - rule_jump_2[1])
        if n_minus1_minus2 in centers_lst:
            neighbors_lst.add(n_minus1_minus2)

        n_minus1_plus2 = (n1[0] + rule_jump_2[0], n1[1] + rule_jump_2[1])
        if n_minus1_plus2 in centers_lst:
            neighbors_lst.add(n_minus1_plus2)

        n_plus1_minus2 = (n2[0] - rule_jump_2[0], n2[1] - rule_jump_2[1])
        if n_plus1_minus2 in centers_lst:
            neighbors_lst.add(n_plus1_minus2)

        n_plus1_plus2 = (n2[0] + rule_jump_2[0], n2[1] + rule_jump_2[1])
        if n_plus1_plus2 in centers_lst:
            neighbors_lst.add(n_plus1_plus2)

        pillar_to_neighbors[p] = list(neighbors_lst)

    return pillar_to_neighbors


def get_pillar_indirect_neighbors_dict(pillar_location):
    """
    Mapping pillar to its indirect neighbors (start from level 2 neighbors)
    :param pillar_location:
    :return:
    """
    pillar_directed_neighbors = get_pillar_directed_neighbors(pillar_location)
    neighbors1, neighbors2 = get_pillar_to_neighbors()
    indirect_neighbors_dict = {}
    for n in neighbors1.keys():
        if n not in pillar_directed_neighbors:
            indirect_neighbors_dict[n] = neighbors1[n]
    for n in neighbors2.keys():
        if n not in pillar_directed_neighbors:
            indirect_neighbors_dict[n] = neighbors2[n]

    return indirect_neighbors_dict


def get_pillar_directed_neighbors(pillar_location):
    """
    Creating a list of a pillar's directed neighbors
    :param pillar_location:
    :return:
    """
    neighbors1, neighbors2 = get_pillar_to_neighbors()
    pillar_directed_neighbors = []
    pillar_directed_neighbors.extend(neighbors1[pillar_location])
    pillar_directed_neighbors.extend(neighbors2[pillar_location])
    pillar_directed_neighbors.append(pillar_location)

    return pillar_directed_neighbors


def get_alive_pillars_to_alive_neighbors():
    """
    Mapping each alive pillar to its level 1 alive neighbors
    :return:
    """
    pillar_to_neighbors = get_pillar_to_neighbors()
    pillar2mask = get_mask_for_each_pillar()
    alive_pillars = get_alive_pillars_lst(pillar2mask)
    alive_pillars_to_alive_neighbors = {}
    for p, nbrs in pillar_to_neighbors.items():
        if p in alive_pillars:
            alive_nbrs = []
            for nbr in nbrs:
                if nbr in alive_pillars:
                    alive_nbrs.append(nbr)
            alive_pillars_to_alive_neighbors[p] = alive_nbrs

    return alive_pillars_to_alive_neighbors


def get_random_neighbors():
    """
    Mapping pillar to new random neighbors (fake neighbors)
    :return:
    """
    pillar_to_nbrs = get_alive_pillars_to_alive_neighbors()
    alive_pillars = list(pillar_to_nbrs.keys())
    new_neighbors_dict = {}

    for pillar, nbrs in pillar_to_nbrs.items():
        num_of_nbrs = len(nbrs)
        if pillar in new_neighbors_dict.keys():
            num_of_nbrs = num_of_nbrs - len(new_neighbors_dict[pillar])
        relevant_pillars = alive_pillars
        relevant_pillars = [p for p in relevant_pillars if p not in nbrs and p != pillar]
        new_nbrs = []
        for i in range(num_of_nbrs):
            new_nbr = random.choice(relevant_pillars)
            new_nbrs.append(new_nbr)
            if new_nbr in new_neighbors_dict.keys():
                new_neighbors_dict[new_nbr].append(pillar)
            else:
                new_neighbors_dict[new_nbr] = [pillar]
            relevant_pillars.remove(new_nbr)
        new_neighbors_dict[pillar] = new_nbrs

    return new_neighbors_dict