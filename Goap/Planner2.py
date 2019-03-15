from Goap.WorldState import WorldState
from Goap.Action import Actions
import networkx as nx


class Node(object):

    def __init__(self, attributes: dict, weight: float = 0.0):
        self.attributes = attributes
        self.weight = weight
        self.name = str(self.attributes)

    def __str__(self):
        return self.name

    def __repr__(self):
        return self.__str__()


class Edge(object):

    def __init__(self, name, predecessor: Node, successor: Node, cost: float = 0.0, obj: object = None):
        self.name = name
        self.cost = cost
        self.predecessor = predecessor
        self.successor = successor
        self.obj = obj

    def __str__(self) -> str:
        return self.name

    def __repr__(self) -> str:
        return self.__str__()


class Nodes(object):

    def __init__(self):
        self.nodes = []

    def __add__(self, other: Node):
        self.nodes.append(other)

    def __iter__(self):
        return self.nodes

    def add(self, other: Node):
        self.__add__(other)


class Edges(object):

    def __init__(self, edges: list = None):
        if edges:
            for edge in edges:
                self.add(edge)
        else:
            self.edges = []

    def __add__(self, other: Edge):
        self.edges.append(other)

    def __iter__(self):
        return self.edges

    def add(self, other: Edge):
        self.__add__(other)


class Graph(object):
    def __init__(self, nodes: list, edges: list):
        self.directed = nx.DiGraph()
        self.add_nodes_from(nodes=nodes)
        self.add_edges_from(edges=edges)
        self.__size = self.size

    def __repr__(self):
        return self.directed

    @staticmethod
    def __is_dst(src: dict, dst: dict) -> bool:
        if src == dst:
            return True
        else:
            return False

    @property
    def size(self):
        return len(self.directed.nodes)

    def __add_node(self, node: Node, attribute: dict):
        self.directed.add_node(node, attr_dict=attribute, label=node.name, object=node)

    def __add_edge(self, edge: Edge):
        self.directed.add_edge(edge.predecessor, edge.successor, object=edge.obj, weight=edge.cost, label=edge.name)

    def add_nodes_from(self, nodes: list):
        [self.__add_node(node, attribute=node.attributes) for node in nodes]

    def add_edges_from(self, edges: list):
        [self.__add_edge(edge=edge) for edge in edges]

    def edge_between_nodes(self, src: str, dst: str, data: bool = True):
        return self.directed.edges(nbunch=(src, dst), data=data)

    def nodes(self, data: bool = True):
        return self.directed.nodes(data=data)

    def edges(self, data: bool = True):
        return self.directed.edges(data=data)

    def search_node(self, attr: dict = None):
        result = None
        if attr:
            for node in self.directed.nodes(data=True):
                if node[1]['attr_dict'].items() == attr.items():
                    result = node[0]
        return result

    def path(self, src: dict, dst: dict):
        if not self.__is_dst(src, dst):
            return nx.astar_path(self.directed, self.search_node(attr=src), self.search_node(attr=dst))

    def plot(self, file_path: str):
        try:
            import matplotlib.pyplot as plt
        except ImportError as err:
            raise('matplotlib not installed. Failed at: {}', err)

        try:
            pos = nx.nx_agraph.graphviz_layout(self.directed)
            nx.draw(
                self.directed,
                pos=pos,
                node_size=1200,
                node_color='lightblue',
                linewidths=0.25,
                font_size=8,
                font_weight='bold',
                with_labels=True,
                dpi=5000
            )
            # edge_labels = nx.get_edge_attributes(self.directed, name='attr_dict')
            # nx.draw_networkx_edge_labels(self.directed, pos=pos, edge_labels=edge_labels)
            plt.savefig(file_path)
        except IOError as err:
            raise('Could not create plot image: {}', err)


class Planner(object):

    def __init__(self, world_state: WorldState, actions: Actions):
        """
        :param actions: list of actions
        """
        # init vars
        self.world_state = world_state
        self.actions = actions
        self.states = self.__generate_states(self.actions, self.world_state)
        self.transitions = self.__generate_transitions(self.actions, self.states)
        self.action_plan = []
        self.graph = Graph(nodes=self.states, edges=self.transitions)

    @staticmethod
    def __isinlist(dic: dict, l: list):
        for d in l:
            if dic == d.attributes:
                return True
        return False

    @staticmethod
    def to_str(dic):
        return str(dic).replace('\'', '')

    def __generate_states(self, actions, world_state):
        states = []
        # if not states:
        #     states.append(Node(attributes=world_state))

        for action in actions:
            pre = {**world_state, **action.pre_conditions}
            eff = {**world_state, **action.effects}
            if not self.__isinlist(pre, states):
                states.append(Node(attributes=pre))
            if not self.__isinlist(eff, states):
                states.append(Node(attributes=eff))
        return states

    # @staticmethod
    # def __generate_transitions(actions, states):
    #     edges = []
    #     pre, suc = None, None
    #     for state in states:
    #         for action in actions:
    #             if action.pre_conditions.items() <= state.attributes.items():
    #                 pre = state
    #             if action.effects.items() <= state.attributes.items():
    #                 suc = state
    #             if pre and suc:
    #                 edges.append(Edge(name=action.name, predecessor=pre, successor=suc, cost=action.cost, obj=action))
    #                 pre, suc = None, None
    #     return edges

    @staticmethod
    def __generate_transitions(actions, states):
        edges = []
        pre, suc = None, None
        for action in actions:
            for state in states:
                if action.pre_conditions.items() <= state.attributes.items():
                    pre = state
                if action.effects.items() <= state.attributes.items():
                    suc = state
                if pre and suc:
                    edges.append(Edge(name=action.name, predecessor=pre, successor=suc, cost=action.cost, obj=action))
                    pre, suc = None, None
        return edges

    @staticmethod
    def __is_end(i: int, l: list) -> bool:
        if i == len(l) - 1:
            return True
        else:
            return False

    def plan(self, state: dict, goal: dict) -> list:
        plan = []
        if state != goal:
            path = self.graph.path(state, goal)
            plan = self.graph.edge_between_nodes(path[0], path[1])
        return plan


if __name__ == '__main__':
    # constants
    init_ws = WorldState(lv_need_expansion=False, vg_need_expansion=False)
    ws = WorldState(lv_need_expansion=True, vg_need_expansion=True)
    gs = WorldState(lv_need_expansion=False, vg_need_expansion=False)

    def setupPlanner():
        acts = Actions()
        acts.add(
            name='ExpandLV',
            pre_conditions={
                'lv_need_expansion': True,
                'vg_need_expansion': False,
            },
            effects={
                'lv_need_expansion': False,
            },
            shell='echo expand_lv',
            cost=1.0
        )
        acts.add(
            name='ExpandVG',
            pre_conditions={
                'vg_need_expansion': True,
            },
            effects={
                'vg_need_expansion': False,
            },
            shell='echo expand_vg'
        )
        acts.add(
            name='PurgeOldFiles',
            pre_conditions={
                'lv_need_expansion': True,
                'vg_need_expansion': True,
            },
            effects={
                'lv_need_expansion': False,
            },
            shell='echo purge_old_files',
            cost=1.5,
        )
        return Planner(world_state=init_ws, actions=acts)

    p = setupPlanner()

    def printNodes(data: bool = True):
        print(p.graph.nodes(data=data))

    def printEdges(data: bool = True):
        print(p.graph.edges(data=data))

    def printSize():
        print(p.graph.size)

    def plotGraph():
        p.graph.plot('graph.png')

    def printWS():
        print(ws)

    def printPath():
        print(p.graph.path(ws, gs))

    def printPlan():
        print(p.plan(ws, gs))

    plotGraph()

    printPath()

    printPlan()

    # print(p.transitions)
    # for t in p.transitions:
    #     print(t.obj)

    # print(p.plan(ws, gs))
    # # print(gs)
    # # print(p.graph.get_node(gs))
    # dir_acts = Actions()
    # dir_acts.add(
    #     name='CreateTmpDir',
    #     pre_conditions={'tmp_dir_state': False, 'tmp_dir_content': False},
    #     effects={'tmp_dir_state': True, 'tmp_dir_content': False},
    #     shell='mkdir -p /tmp/goap_tmp'
    # )
    # dir_acts.add(
    #     name='CreateToken',
    #     pre_conditions={'tmp_dir_state': True, 'tmp_dir_content': False},
    #     effects={'tmp_dir_state': True, 'tmp_dir_content': True},
    #     shell='touch /tmp/goap_tmp/.token'
    # )
    # dir_init_ws = WorldState({"tmp_dir_state": False, "tmp_dir_content": False, })
    # dir_gs = WorldState({"tmp_dir_state": True, "tmp_dir_content": True, })
    # dir_handler = Planner(world_state=dir_init_ws, actions=dir_acts)
    # print(dir_handler.graph.nodes(data=True))
    # print(dir_handler.graph.size)
    # print(dir_handler.graph.edges(data=True))
    # print(dir_handler.graph.path(dir_init_ws, dir_gs))
