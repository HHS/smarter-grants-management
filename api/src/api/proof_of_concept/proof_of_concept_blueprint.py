from apiflask import APIBlueprint

proof_of_concept_blueprint = APIBlueprint(
    "proof_of_concept_alpha",
    __name__,
    tag="Proof of Concept - Alpha",
    cli_group="proof_of_concept_alpha",
    url_prefix="/alpha/proof_of_concept",
)
