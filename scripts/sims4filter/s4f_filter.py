import traceback
from typing import Callable, Dict, Tuple, Type, Union

import services
import sims4.commands
from sims.global_gender_preference_tuning import GlobalGenderPreferenceTuning
from sims.occult.occult_enums import OccultType
from sims.sim_info import SimInfo
from sims.sim_info_manager import SimInfoManager
from sims.sim_info_types import Age, Gender, SpeciesExtended

from s4f_base_classes import SimFilter, SimTransformer, SimFilterKeyword
from s4f_logic import Logic
from s4f_postfix_parser import TinyParser


try:

    class Tools:
        @staticmethod
        def get_gender_preference(sim_info: SimInfo, gender: Gender) -> float:
            """
            Return the gender preference value in floating point, between -100 to 100, for a given SimInfo and Gender.

            @param sim_info: The SimInfo object to get the gender preference for.
            @param gender: The Gender enum value to get the preference for.
            @return: The gender preference value in floating point, between -100 to 100.
            """
            tracker_gender_pref = sim_info.get_tracker(
                GlobalGenderPreferenceTuning.GENDER_PREFERENCE[gender]  # pyright: ignore[reportIndexIssue]
            )
            gender_pref = tracker_gender_pref.get_value(  # pyright: ignore[reportOptionalMemberAccess]
                GlobalGenderPreferenceTuning.GENDER_PREFERENCE[gender]  # pyright: ignore[reportIndexIssue]
            )
            return gender_pref

        @staticmethod
        def is_culled(sim_info: SimInfo) -> bool:
            """
            Check if the SimInfo object is culled.
            A sim is culled when it is a ghost and has no trackers.

            @param sim_info: The SimInfo object to check.
            @return: True if the sim is culled, False otherwise.
            """
            if sim_info.is_ghost and sim_info.commodity_tracker is None:
                return True
            return False

        @staticmethod
        def home_world(sim_info: SimInfo) -> str:
            """
            Get the home world of the SimInfo object.

            @param sim_info: The SimInfo object to get the home world for.
            @return: The home world of the sim as a string.
            """
            persistence_service = services.get_persistence_service()
            neighborhood_data = (
                persistence_service.get_neighborhood_proto_buf_from_zone_id(
                    sim_info.household.home_zone_id  # pyright: ignore[reportOptionalMemberAccess]
                )
            )
            if neighborhood_data is None:
                return "Unknown"
            return neighborhood_data.name

    class FilteredSims:
        """
        A class to filter SimInfo objects based on specified filters
        """

        def __init__(self):
            self._sim_info_manager: SimInfoManager = services.sim_info_manager()
            self._starter_list: list[SimInfo] = list(self._sim_info_manager.get_all())
            self._filtered_sims: filter[SimInfo] = filter(
                lambda x: x is not None and isinstance(x, SimInfo), self._starter_list
            )

        def filter(self, filter_func: Callable[[SimInfo], bool]) -> None:
            """
            Apply a filter function to the current set of filtered Sims.

            @param filter_func: A function that takes a SimInfo object and returns a boolean indicating
                                whether the object should be included in the filtered results.
            @return:            None
            @example
            from sims.sim_info_types

            def is_adult(sim: SimInfo) -> bool:
                return sim.age >= Age.YOUNGADULT

            filtered_sims = FilteredSims()
            filtered_sims.filter(is_adult)
            for sim_info in filtered_sims:
                print(sim_info.sim_id)
            """
            self._filtered_sims = filter(filter_func, self._filtered_sims)

        def transform(self, transform_func: Callable[[SimInfo], SimInfo]) -> None:
            self._filtered_sims = filter(
                lambda x: x is not None and isinstance(x, SimInfo),
                map(transform_func, self._filtered_sims),
            )

        def __iter__(self):
            """
            Iterate over the filtered Sims.
            Once you have started iterating, the filtered_sims class is now defunct and cannot be reused.
            """
            return self

        def __next__(self):
            """
            Iterate over the filtered Sims.
            Once you have started iterating, the filtered_sims class is now defunct and cannot be reused.
            """
            return next(self._filtered_sims)

    class FilterAge(SimFilter):
        def __init__(self, keyword: SimFilterKeyword, age: Age):
            super().__init__()
            self._keyword = keyword
            self._age = age

        def __call__(self, sim: SimInfo) -> bool:
            try:
                # if not hasattr(sim, "age"):
                #     return False
                # if not isinstance(sim.age, Age):
                #     return False
                if self._keyword == SimFilterKeyword.EQUALS:
                    return sim.age == self._age
                elif self._keyword == SimFilterKeyword.GREATER_THAN:
                    return sim.age > self._age
                elif self._keyword == SimFilterKeyword.LESS_THAN:
                    return sim.age < self._age
                else:
                    raise ValueError(f"Unknown keyword: {self._keyword}")
            except Exception:
                return False

    class FilterGender(SimFilter):
        def __init__(self, gender: Gender):
            super().__init__()
            self._gender = gender

        def __call__(self, sim: SimInfo) -> bool:
            try:
                # if not hasattr(sim, "gender"):
                #     return False
                # if not isinstance(sim.gender, Gender):
                #     return False
                return sim.gender == self._gender
            except Exception:
                return False

    class FilterGenderPreference(SimFilter):
        def __init__(self, keyword: SimFilterKeyword, gender: Gender, preference: int):
            super().__init__()
            self._keyword = keyword
            self._gender = gender
            self._preference = preference

        def __call__(self, sim: SimInfo) -> bool:
            try:
                gender_pref = Tools.get_gender_preference(sim, self._gender)
                if self._keyword == SimFilterKeyword.EQUALS:
                    return gender_pref == self._preference
                elif self._keyword == SimFilterKeyword.LESS_THAN:
                    return gender_pref < self._preference
                elif self._keyword == SimFilterKeyword.GREATER_THAN:
                    return gender_pref > self._preference
                else:
                    raise ValueError(f"Unknown keyword: {self._keyword}")
            except Exception:
                return False

    class FilterFirstName(SimFilter):
        def __init__(self, keyword: SimFilterKeyword, first_name: str):
            super().__init__()
            self._keyword = keyword
            self._first_name = first_name

        def __call__(self, sim: SimInfo) -> bool:
            try:
                # if not hasattr(sim, "first_name"):
                #     return False
                # if not isinstance(sim.first_name, str):
                #     return False
                if self._keyword == SimFilterKeyword.EQUALS:
                    return sim.first_name.lower() == self._first_name  # pyright: ignore[reportAttributeAccessIssue]
                elif self._keyword == SimFilterKeyword.CONTAINS:
                    return self._first_name in sim.first_name.lower()  # pyright: ignore[reportAttributeAccessIssue]
                else:
                    raise ValueError(f"Unknown keyword: {self._keyword}")
            except Exception:
                return False

    class FilterLastName(SimFilter):
        def __init__(self, keyword: SimFilterKeyword, last_name: str):
            super().__init__()
            self._keyword = keyword
            self._last_name = last_name

        def __call__(self, sim: SimInfo) -> bool:
            try:
                # if not hasattr(sim, "last_name"):
                #     return False
                # if not isinstance(sim.last_name, str):
                #     return False
                if self._keyword == SimFilterKeyword.EQUALS:
                    return sim.last_name.lower() == self._last_name  # pyright: ignore[reportAttributeAccessIssue]
                elif self._keyword == SimFilterKeyword.CONTAINS:
                    return self._last_name in sim.last_name.lower()  # pyright: ignore[reportAttributeAccessIssue]
                else:
                    raise ValueError(f"Unknown keyword: {self._keyword}")
            except Exception:
                return False

    class FilterSimID(SimFilter):
        def __init__(self, sim_id: int):
            super().__init__()
            self._sim_id = sim_id

        def __call__(self, sim: SimInfo) -> bool:
            try:
                # if not hasattr(sim, "id"):
                #     return False
                # if not isinstance(sim.id, int):
                #     return False
                return sim.sim_id == self._sim_id
            except Exception:
                return False

    class FilterOccult(SimFilter):
        def __init__(self, occult: OccultType):
            super().__init__()
            self._occult = occult

        def __call__(self, sim: SimInfo) -> bool:
            try:
                # if not hasattr(sim, "occult_types"):
                #     return False
                # if not isinstance(sim.occult_types, OccultType):
                #     return False
                return sim.occult_types & self._occult == self._occult
            except Exception:
                return False

    class FilterIsSim(SimFilter):
        def __init__(self):
            super().__init__()

        def __call__(self, sim: SimInfo) -> bool:
            try:
                return isinstance(sim, SimInfo)
            except Exception:
                return False

    class FilterCulled(SimFilter):
        def __call__(self, sim: SimInfo) -> bool:
            try:
                return Tools.is_culled(sim)
            except Exception:
                return False

    class FilterPregnant(SimFilter):
        def __call__(self, sim: SimInfo) -> bool:
            try:
                # if not hasattr(sim, "is_pregnant"):
                #     return False
                # if not isinstance(sim.is_pregnant, bool):
                #     return False
                return sim.is_pregnant
            except Exception:
                return False

    class FilterPregnancyProgress(SimFilter):
        def __init__(self, keyword: SimFilterKeyword, progress: int):
            super().__init__()
            self._keyword = keyword
            self._progress = progress

        def __call__(self, sim: SimInfo) -> bool:
            try:
                if not sim.is_pregnant:
                    return False
                progress = sim.pregnancy_progress * 100  # pyright: ignore[reportOperatorIssue]
                if self._keyword == SimFilterKeyword.EQUALS:
                    return progress == self._progress
                elif self._keyword == SimFilterKeyword.GREATER_THAN:
                    return progress > self._progress
                elif self._keyword == SimFilterKeyword.LESS_THAN:
                    return progress < self._progress
                else:
                    raise ValueError(f"Unknown keyword: {self._keyword}")
            except Exception:
                return False

    class FilterSpecies(SimFilter):
        def __init__(self, species: SpeciesExtended):
            super().__init__()
            self._species = species

        def __call__(self, sim: SimInfo) -> bool:
            try:
                if self._species == SpeciesExtended.HUMAN:
                    return sim.species == SpeciesExtended.HUMAN
                return sim.extended_species == self._species
            except Exception:
                return False

    class FilterBreed(SimFilter):
        def __init__(self, breed: str):
            super().__init__()
            self._breed = breed

        def __call__(self, sim: SimInfo) -> bool:
            try:
                if self._breed in sim.breed_name.lower():  # pyright: ignore[reportAttributeAccessIssue, reportOperatorIssue]
                    return True
                return False
            except Exception:
                return False

    class FilterHomeWorld(SimFilter):
        def __init__(self, home_world: str):
            super().__init__()
            self._home_world = home_world

        def __call__(self, sim: SimInfo) -> bool:
            try:
                return self._home_world.lower() in Tools.home_world(sim).lower()
            except Exception:
                return False

    class TransformerSpouse(SimTransformer):
        """
        Transforms a SimInfo object to its spouse SimInfo if it exists.
        """

        def __call__(self, sim: SimInfo) -> Union[SimInfo, None]:
            try:
                spouse = sim.get_spouse_sim_info()
                if not isinstance(spouse, SimInfo):
                    return None
                return spouse
            except Exception:
                return None

    class TransformerPartner(SimTransformer):
        """
        Transforms a SimInfo object to its pregnancy partner SimInfo if it exists.
        """

        def __call__(self, sim: SimInfo) -> Union[SimInfo, None]:
            try:
                if not sim.is_pregnant:
                    return None
                partner = sim.pregnancy_tracker().get_partner()  # pyright: ignore[reportOptionalCall]
                if not isinstance(partner, SimInfo):
                    return None
                return partner
            except Exception:
                return None

    @staticmethod
    def parse_option_age(text: str) -> Tuple[SimFilterKeyword, Age]:
        for op_key, op_val in operator_keywords.items():
            if op_key in text:
                operator, value = text.split(op_key)
                break
        else:
            raise ValueError(f"Invalid age filter expression: {text}")
        age = Age.name_to_value.get(value.upper(), None)
        if age is None:
            raise ValueError(f"Invalid age: {value}")
        return (op_val, age)

    @staticmethod
    def parse_option_genderprefmale(text: str) -> Tuple[SimFilterKeyword, Gender, int]:
        for op_key, op_val in operator_keywords.items():
            if op_key in text:
                operator, value = text.split(op_key)
                break
        else:
            raise ValueError(f"Invalid age filter expression: {text}")
        return (op_val, Gender(Gender.MALE), int(value))

    @staticmethod
    def parse_option_genderpreffemale(
        text: str,
    ) -> Tuple[SimFilterKeyword, Gender, int]:
        for op_key, op_val in operator_keywords.items():
            if op_key in text:
                operator, value = text.split(op_key)
                break
        else:
            raise ValueError(f"Invalid age filter expression: {text}")
        return (op_val, Gender(Gender.FEMALE), int(value))

    @staticmethod
    def parse_option_pregnancyprogress(text: str) -> Tuple[SimFilterKeyword, int]:
        for op_key, op_val in operator_keywords.items():
            if op_key in text:
                operator, value = text.split(op_key)
                break
        else:
            raise ValueError(f"Invalid age filter expression: {text}")
        return (op_val, int(value))

    @staticmethod
    def parse_option_firstname(text: str) -> Tuple[SimFilterKeyword, str]:
        for op_key, op_val in operator_keywords.items():
            if op_key in text:
                operator, value = text.split(op_key)
                break
        else:
            raise ValueError(f"Invalid age filter expression: {text}")
        return (op_val, value)

    @staticmethod
    def parse_option_lastname(text: str) -> Tuple[SimFilterKeyword, str]:
        for op_key, op_val in operator_keywords.items():
            if op_key in text:
                operator, value = text.split(op_key)
                break
        else:
            raise ValueError(f"Invalid age filter expression: {text}")
        return (op_val, value)

    @staticmethod
    def parse_option_homeworld(text: str) -> Tuple[str]:
        for op_key, op_val in operator_keywords.items():
            if op_key in text:
                operator, value = text.split(op_key)
                break
        else:
            raise ValueError(f"Invalid homeworld filter expression: {text}")
        return (value,)

    def token_parser(text: str) -> Union[SimFilter, SimTransformer]:
        if text in cached_map:
            return cached_map[text]
        operator_filters: Dict[
            str,
            Tuple[Union[Type[SimFilter], Type[SimTransformer]], Callable[[str], Tuple]],
        ] = {  # NB: Make sure no words are prefixes of another word
            "age": (FilterAge, parse_option_age),
            "world": (FilterHomeWorld, parse_option_homeworld),
            "firstname": (FilterFirstName, parse_option_firstname),
            "lastname": (FilterLastName, parse_option_lastname),
            "pregnancyprogress": (
                FilterPregnancyProgress,
                parse_option_pregnancyprogress,
            ),
            "prefmale": (FilterGenderPreference, parse_option_genderprefmale),
            "preffemale": (FilterGenderPreference, parse_option_genderpreffemale),
        }
        for filter_name in operator_filters.keys():
            if text.startswith(filter_name):
                sim_filter = operator_filters[filter_name][0]
                args = operator_filters[filter_name][1](text)
                return sim_filter(*args)
        raise ValueError(f"Unknown filter: {text}")

    cached_map = {
        "is_sim": FilterIsSim(),
        "culled": FilterCulled(),
        "spouse": TransformerSpouse(),
        "partner": TransformerPartner(),
        "male": FilterGender(Gender(Gender.MALE)),
        "female": FilterGender(Gender(Gender.FEMALE)),
        "elder": FilterAge(SimFilterKeyword.EQUALS, Age(Age.ELDER)),
        "adult": FilterAge(SimFilterKeyword.EQUALS, Age(Age.ADULT)),
        "youngadult": FilterAge(SimFilterKeyword.EQUALS, Age(Age.YOUNGADULT)),
        "teen": FilterAge(SimFilterKeyword.EQUALS, Age(Age.TEEN)),
        "child": FilterAge(SimFilterKeyword.EQUALS, Age(Age.CHILD)),
        "toddler": FilterAge(SimFilterKeyword.EQUALS, Age(Age.TODDLER)),
        "baby": FilterAge(SimFilterKeyword.EQUALS, Age(Age.BABY)),
        "infant": FilterAge(SimFilterKeyword.EQUALS, Age(Age.INFANT)),
        "pregnant": FilterPregnant(),
        "human": FilterSpecies(SpeciesExtended(SpeciesExtended.HUMAN)),
        "dog": FilterSpecies(SpeciesExtended(SpeciesExtended.DOG)),
        "smalldog": FilterSpecies(SpeciesExtended(SpeciesExtended.SMALLDOG)),
        "cat": FilterSpecies(SpeciesExtended(SpeciesExtended.CAT)),
        "horse": FilterSpecies(SpeciesExtended(SpeciesExtended.HORSE)),
        "fox": FilterSpecies(SpeciesExtended(SpeciesExtended.FOX)),
        "vampire": FilterOccult(OccultType(OccultType.VAMPIRE)),
        "werewolf": FilterOccult(OccultType(OccultType.WEREWOLF)),
        "witch": FilterOccult(OccultType(OccultType.WITCH)),
        "alien": FilterOccult(OccultType(OccultType.ALIEN)),
        "mermaid": FilterOccult(OccultType(OccultType.MERMAID)),
        "fairy": FilterOccult(OccultType(OccultType.FAIRY)),
        "nooccult": Logic.negation(
            Logic.conjunction(
                FilterOccult(OccultType(OccultType.VAMPIRE)),
                FilterOccult(OccultType(OccultType.WEREWOLF)),
                FilterOccult(OccultType(OccultType.WITCH)),
                FilterOccult(OccultType(OccultType.ALIEN)),
                FilterOccult(OccultType(OccultType.MERMAID)),
                FilterOccult(OccultType(OccultType.FAIRY)),
            )
        ),
    }
    operator_keywords = {
        "=": SimFilterKeyword.EQUALS,
        "<": SimFilterKeyword.LESS_THAN,
        ">": SimFilterKeyword.GREATER_THAN,
        ":": SimFilterKeyword.CONTAINS,
    }

    @sims4.commands.Command("s4f.filter", command_type=sims4.commands.CommandType.Live)
    def s4f_filter(
        *args,
        _connection=None,
    ):
        output = sims4.commands.CheatOutput(_connection)
        from ita_common_lib import Localization, OperationHistory
        from Ita_ShowSimInfo3 import SimPickerDialog
        from ita_const import StringTable as STBL

        try:
            output(f"Got arguments: {args}")
            parser = TinyParser(args, token_parser)  # pyright: ignore[reportArgumentType]
            filter = parser.parse()
            fsims = FilteredSims()
            fsims.filter(filter)
            sim_infos = [sim for sim in fsims]
            # for sim in sim_infos:
            #     output(f"pregnancy progress {sim.first_name} {sim.last_name} = {sim.pregnancy_progress}")
            OperationHistory.updateHistory()
            hashDescription = Localization.createHash(STBL.RESULT_OF_SEARCH, "")
            SimPickerDialog.show_relation_picker(
                sim_infos, "callback", None, hashDescription
            )
            # spouse pregnant compose_filter pregnant or male spouse male compose_filter and and
            # from mc_cheats import CheatsModule
            # for sim in sim_infos:
            #     CheatsModule.summon_sim(sim_info=sim)

            for sim in sim_infos:
                output(
                    f"Sim ID: {sim.id} Name: {sim.first_name} {sim.last_name} - {Tools.home_world(sim)}"
                )
        except Exception as e:
            output(f"Error filtering Sims: {e} - {traceback.format_exc()}")

except:  # noqa: E722, ignore[bare-except]
    pass
