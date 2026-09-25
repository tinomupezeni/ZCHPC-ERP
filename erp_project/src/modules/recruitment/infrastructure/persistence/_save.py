"""
Aggregate persistence that never chooses a primary key.

The recruitment repositories used to mint IDs as max(id) + 1 and write with
update_or_create(id=...). Two concurrent submissions could compute the same
ID, and the second then *updated* the first one's row - replacing another
person's candidate identity or application. REM-04 made that reachable
anonymously.

The rule now: a new aggregate (id is None) is always INSERTed and receives a
database-assigned key; an aggregate with an id only ever updates that
existing row, and a missing row is an error, never an implicit insert.
"""

from shared.domain.exceptions import NotFoundError


def insert_or_update(model_class, entity_id, fields: dict):
    if entity_id is None:
        return model_class.objects.create(**fields)

    try:
        model = model_class.objects.get(pk=entity_id)
    except model_class.DoesNotExist:
        raise NotFoundError(
            f"{model_class.__name__} with ID {entity_id} does not exist"
        ) from None

    for name, value in fields.items():
        setattr(model, name, value)
    model.save()
    return model
