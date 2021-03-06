"""
Functions for error chain reconstruction
"""


def reconstruct_all_error_chains(errorregistry, callgraph):
    """
    Calculate a dict of vulnerable instruction => [error chains]
    """

    result = dict()
    for vulninst, errorlist in errorregistry.forvulninst.items():
        # Get all chains for this vulnerable instruction
        chains = reconstruct_error_chain(errorlist, callgraph)

        # Sort by chain length and then alphabetically
        result[vulninst] = sorted(chains, key=lambda x: (-len(x), "@".join(x)))

    return result


def reconstruct_error_chain(errorlist, callgraph):
    """
    Calculate a list of all error chains inside a given errorlist
    """
    # Collect a set of affected functions
    affected = set({error.entryfunction for error in errorlist})

    # Find all heads of the chains
    chains = [[fun] for fun in affected if not any(
        call in affected for call in callgraph[fun]['calls'])]

    # If we don't find a head for the error, it must be a circle
    if not chains:
        # A bit hacky, because we might circles over multiple functions
        chains = [[fun] for fun in affected if not any(
            call in affected and call != fun
            for call in callgraph[fun]['calls'])]

    # Extent all chains, until all callers are no longer infected
    for calleelist in callgraph.group_independent_callees():
        # Create storage for old and new chains
        oldchains = list(chains)
        newchains = list()

        # Try to continue each chain
        for chain in oldchains:
            extended = False
            if chain[-1] in calleelist:
                for nextnode in callgraph[chain[-1]]['calledby']:
                    if nextnode in affected:
                        newchains.append(chain[:] + [nextnode])
                        extended = True

            if not extended:
                # Leave the current chain untouched
                newchains.append(chain[:])
        chains = newchains
    return chains
