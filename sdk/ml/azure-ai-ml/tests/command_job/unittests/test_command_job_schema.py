from azure.ai.ml._schema import CommandJobSchema
from azure.ai.ml._utils.utils import load_yaml, is_valid_uuid
from azure.ai.ml.constants import BASE_PATH_CONTEXT_KEY
from azure.ai.ml.entities import CommandJob
from azure.ai.ml.entities._inputs_outputs import Input
from pathlib import Path
from azure.ai.ml import load_job
from marshmallow.exceptions import ValidationError
import yaml
import pytest


@pytest.mark.unittest
class TestCommandJob:
    def test_deserialize(self):
        test_path = "./tests/test_configs/command_job/command_job_test.yml"
        with open("./tests/test_configs/command_job/command_job_rest.yml", "r") as f:
            target = yaml.safe_load(f)
        with open(test_path, "r") as f:
            cfg = yaml.safe_load(f)
            context = {BASE_PATH_CONTEXT_KEY: Path(test_path).parent}
            schema = CommandJobSchema(context=context)
            internal_representation: CommandJob = CommandJob(**schema.load(cfg))
        source = internal_representation._to_rest_object()
        assert source.name == target["name"]
        assert source.properties.command == target["properties"]["command"]

    def test_distributions_roundtrip(self):
        paths = [
            "./tests/test_configs/command_job/dist_job_1.yml",
            "./tests/test_configs/command_job/dist_job_2.yml",
            "./tests/test_configs/command_job/dist_job_3.yml",
        ]
        context = {BASE_PATH_CONTEXT_KEY: Path(paths[0]).parent}
        schema = CommandJobSchema(context=context)
        cfg = None

        for path in paths:
            with open(path, "r") as f:
                cfg = yaml.safe_load(f)
            internal_representation: CommandJob = CommandJob(**schema.load(cfg))
            rest_intermediate = internal_representation._to_rest_object()
            internal_obj = CommandJob._from_rest_object(rest_intermediate)
            internal_obj._id = "test-arm-id"
            reconstructed_yaml = schema.dump(internal_obj)
            assert reconstructed_yaml["distribution"]["type"].lower() == cfg["distribution"]["type"].lower()
            reconstructed_yaml["distribution"].pop("type")
            cfg["distribution"].pop("type")
            assert reconstructed_yaml["distribution"] == cfg["distribution"]
            reconstructed_yaml["resources"].pop("properties")  # pop out the empty properties dict
            assert reconstructed_yaml["resources"] == cfg["resources"]
            assert reconstructed_yaml["limits"] == cfg["limits"]

    def test_invalid_distribution_config(self):
        path = "./tests/test_configs/command_job/dist_job_bad.yml"
        context = {BASE_PATH_CONTEXT_KEY: Path(path).parent}
        schema = CommandJobSchema(context=context)
        with open(path, "r") as f:
            cfg = yaml.safe_load(f)
            with pytest.raises(ValidationError):
                CommandJob(**schema.load(cfg))

    def test_deserialize_inputs(self):
        test_path = "./tests/test_configs/command_job/command_job_inputs_test.yml"
        with open("./tests/test_configs/command_job/command_job_inputs_rest.yml", "r") as f:
            target = yaml.safe_load(f)
        with open(test_path, "r") as f:
            cfg = yaml.safe_load(f)
            context = {BASE_PATH_CONTEXT_KEY: Path(test_path).parent}
            schema = CommandJobSchema(context=context)
            internal_representation: CommandJob = CommandJob(**schema.load(cfg))
        source = internal_representation._to_rest_object()
        assert source.properties.inputs["test1"].uri == target["properties"]["inputs"]["test1"]["uri"]

    def test_deserialize_inputs_dataset(self):
        test_path = "./tests/test_configs/command_job/command_job_inputs_dataset_test.yml"
        with open("./tests/test_configs/command_job/command_job_inputs_dataset_test.yml", "r") as f:
            target = yaml.safe_load(f)
        with open(test_path, "r") as f:
            cfg = yaml.safe_load(f)
            context = {BASE_PATH_CONTEXT_KEY: Path(test_path).parent}
            schema = CommandJobSchema(context=context)
            internal_representation: CommandJob = CommandJob(**schema.load(cfg))
        source = internal_representation._to_rest_object()
        assert source.properties.inputs["test1"].uri == target["inputs"]["test1"]["path"]

    def test_anonymous_assets(self):
        test_path = "./tests/test_configs/command_job/inlined_assets.yaml"
        with open(test_path, "r") as f:
            cfg = yaml.safe_load(f)

        # Grab original names from yaml, they should be dropped on deserialize
        envName = cfg["environment"]["name"]
        code = cfg["code"]
        input_path = cfg["inputs"]["test1"]["path"]

        internal_representation: CommandJob = load_job(path=test_path)

        # anonymous environments are created with name CliV2AnonymousEnvironment and a guid as the version
        assert internal_representation.environment.name != envName
        assert internal_representation.environment.name == "CliV2AnonymousEnvironment"
        assert internal_representation.environment._is_anonymous
        assert internal_representation.environment.version == "559c904a18d86cc54f2f6a9d6ac26c0d"

        assert internal_representation.inputs["test1"].path == input_path
        # Validate default dataset is mounted
        assert internal_representation.inputs["test1"].mode == "ro_mount"
        assert internal_representation.code == code

    def test_deserialize_amltoken_identity(self):
        test_path = "./tests/test_configs/command_job/command_job_test_amltoken_identity.yml"
        with open("./tests/test_configs/command_job/command_job_rest_amltoken_identity.yml", "r") as f:
            target = yaml.safe_load(f)
        with open(test_path, "r") as f:
            cfg = yaml.safe_load(f)
            context = {BASE_PATH_CONTEXT_KEY: Path(test_path).parent}
            schema = CommandJobSchema(context=context)
            internal_representation: CommandJob = CommandJob(**schema.load(cfg))
        source = internal_representation._to_rest_object()
        assert source.properties.identity.identity_type == target["properties"]["identity"]["identity_type"]

    def test_deserialize_msi_identity(self):
        test_path = "./tests/test_configs/command_job/command_job_test_msi_identity.yml"
        with open("./tests/test_configs/command_job/command_job_rest_msi_identity.yml", "r") as f:
            target = yaml.safe_load(f)
        with open(test_path, "r") as f:
            cfg = yaml.safe_load(f)
            context = {BASE_PATH_CONTEXT_KEY: Path(test_path).parent}
            schema = CommandJobSchema(context=context)
            internal_representation: CommandJob = CommandJob(**schema.load(cfg))
        source = internal_representation._to_rest_object()
        assert source.properties.identity.identity_type == target["properties"]["identity"]["identity_type"]
        assert source.properties.identity.client_id == target["properties"]["identity"]["client_id"]

    def test_file_environments(self):
        test_path = "./tests/test_configs/command_job/command_job_test_yaml_ref.yml"
        with open(test_path, "r") as f:
            cfg = yaml.safe_load(f)
        env_path = "./tests/test_configs/environment/environment_conda.yml"
        with open(env_path, "r") as f:
            env = yaml.safe_load(f)

        conda_text = load_yaml(Path("./tests/test_configs/environment/environment_files/environment.yml"))

        envName = env["name"]
        envImage = env["image"]

        context = {BASE_PATH_CONTEXT_KEY: Path(test_path).parent}
        schema = CommandJobSchema(context=context)
        internal_representation: CommandJob = CommandJob(**schema.load(cfg))
        # inline envs should ignore set name, and be anonymous
        assert internal_representation.environment.name != envName
        # referenced yaml should be loaded
        assert internal_representation.environment.image == envImage
        # path referenced within child yaml should be resolved relative to child yaml
        assert internal_representation.environment.conda_file == conda_text

    def test_input_is_loaded_from_dictionary(self):
        command_job = CommandJob(
            code="./src",
            command="python train.py --ss {search_space.ss}",
            inputs={
                "input1": {
                    "type": "uri_file",
                    "path": "../testdata.txt",
                }
            },
            compute="local",
            environment="AzureML-sklearn-0.24-ubuntu18.04-py37-cpu:1",
        )
        assert isinstance(command_job.inputs["input1"], Input)

    def test_input_data_path_resolution(self):
        test_path = "./tests/test_configs/command_job/command_job_relative_inputs_test.yml"
        with open(test_path, "r") as f:
            cfg = yaml.safe_load(f)
        context = {BASE_PATH_CONTEXT_KEY: Path(test_path).parent}
        schema = CommandJobSchema(context=context)
        internal_representation: CommandJob = CommandJob(**schema.load(cfg))

        assert internal_representation.inputs["test1"].path == "../python/sample1.csv"
