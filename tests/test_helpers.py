from dataclasses import asdict
import logging
import os

import pytest

from ..pyramid_api.api_types import (
    NewTenant
)

from ..pyramid_api.helper_types import (
    WrappedType
)


LOG = logging.getLogger(__name__)

TEST_ARTIFACT_PATH = './tests/tmp'

@pytest.mark.unit
@pytest.mark.helpers
def test__wrap_type():
    obj = NewTenant(
        '$tenantId',
        '$tenantName',
        1,
        1,
        True
    )
    wrapped_instance = WrappedType.create(obj)
    new_instance = wrapped_instance.to_instance()
    assert(new_instance == obj)
    file_path = None
    try:
        os.mkdir(TEST_ARTIFACT_PATH)
        file_path = f'{TEST_ARTIFACT_PATH}/__test_newtenant_instance.json'
        wrapped_instance.to_file(file_path)
        from_file = WrappedType.createFromFile(file_path)
        assert(from_file == wrapped_instance)
        values = {
            'tenantId': 'mytenantid',
            'tenantName': 'mytenant'
        }
        # full template
        templated_from_file = WrappedType.createFromFile(file_path, values)
        assert(templated_from_file != wrapped_instance)
        resolved_instance = templated_from_file.to_instance()
        assert(resolved_instance.id == values['tenantId']) 
        # missing value
        del values['tenantName']
        with pytest.raises(KeyError):
            templated_from_file = WrappedType.createFromFile(file_path, values)
        templated_from_file = WrappedType.createFromFile(file_path, values, False)
        assert(templated_from_file != wrapped_instance)
        resolved_instance = templated_from_file.to_instance()
        assert(resolved_instance.id == values['tenantId']) 

    finally:
        LOG.debug(from_file)
        if file_path:
            os.remove(file_path)
        os.rmdir(TEST_ARTIFACT_PATH)


