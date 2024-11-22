import ast
import json


class RedisUtils(object):
    @staticmethod
    def encode_nested_dict(struct: dict) -> dict:
        encoded_dict = {}

        for k in struct:
            if isinstance(struct[k], (dict, list, tuple)):
                encoded_dict[k] = json.dumps(struct[k])
            else:
                encoded_dict[k] = struct[k]
        return encoded_dict

    # noinspection PyBroadException
    @classmethod
    def decode_redis_output(
        cls,
        src: list | dict | bytes | None,
    ) -> list | dict | str | None:
        """
        Helper function to decode output from Redis backend.

        Args:
            src: redis output to decode

        Returns:
            A list, dict or str with decoded output or None if src is None.
        """

        if isinstance(src, list):
            rv = list()
            for key in src:
                rv.append(cls.decode_redis_output(key))
            return rv
        elif isinstance(src, dict):
            rv = dict()
            for key in src:
                if not isinstance(key, str):
                    rv[key.decode()] = cls.decode_redis_output(src[key])
                else:
                    rv[key] = cls.decode_redis_output(src[key])
            return rv
        elif isinstance(src, bytes):
            try:
                return ast.literal_eval(src.decode())
            except ValueError:
                # possibly JSON serialized
                try:
                    return json.loads(src.decode())
                except Exception:
                    return src.decode()
            except Exception:
                return src.decode()
        elif src is None:
            return src
        else:
            raise Exception(f"type not handled: {type(src)}")
