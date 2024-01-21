
def tortoise_to_pydantic(tortoise_model, pydantic_model, **kwargs):
    fields_map = {field: getattr(tortoise_model, field) for field in pydantic_model.__annotations__ if
                  hasattr(tortoise_model, field)}

    # Создаем экземпляр Pydantic-модели без kwargs
    pydantic_instance = pydantic_model(**fields_map, **kwargs)

    # Обновляем значения из kwargs
    for key, value in kwargs.items():
        if hasattr(pydantic_instance, key):
            setattr(pydantic_instance, key, value)

    return pydantic_instance
