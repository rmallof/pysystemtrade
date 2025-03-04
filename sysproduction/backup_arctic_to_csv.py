import os
import pandas as pd

from syscore.pdutils import check_df_equals, check_ts_equals
from syscore.objects import missing_data
from syscore.dateutils import CALENDAR_DAYS_IN_YEAR
from sysdata.data_blob import dataBlob

from sysdata.csv.csv_futures_contracts import csvFuturesContractData
from sysdata.csv.csv_adjusted_prices import csvFuturesAdjustedPricesData
from sysdata.csv.csv_futures_contract_prices import csvFuturesContractPriceData
from sysdata.csv.csv_multiple_prices import csvFuturesMultiplePricesData
from sysdata.csv.csv_spot_fx import csvFxPricesData
from sysdata.csv.csv_contract_position_data import csvContractPositionData
from sysdata.csv.csv_strategy_position_data import csvStrategyPositionData
from sysdata.csv.csv_historic_orders import (
    csvStrategyHistoricOrdersData,
    csvContractHistoricOrdersData,
    csvBrokerHistoricOrdersData,
)
from sysdata.csv.csv_capital_data import csvCapitalData
from sysdata.csv.csv_optimal_position import csvOptimalPositionData
from sysdata.csv.csv_instrument_data import csvFuturesInstrumentData
from sysdata.csv.csv_roll_state_storage import csvRollStateData
from sysdata.csv.csv_spreads import csvSpreadsForInstrumentData

from sysdata.arctic.arctic_futures_per_contract_prices import (
    arcticFuturesContractPriceData,
)
from sysdata.arctic.arctic_multiple_prices import arcticFuturesMultiplePricesData
from sysdata.arctic.arctic_adjusted_prices import arcticFuturesAdjustedPricesData
from sysdata.arctic.arctic_spotfx_prices import arcticFxPricesData
from sysdata.arctic.arctic_spreads import arcticSpreadsForInstrumentData
from sysdata.arctic.arctic_capital import arcticCapitalData

from sysdata.mongodb.mongo_futures_contracts import mongoFuturesContractData
from sysdata.mongodb.mongo_position_by_contract import mongoContractPositionData
from sysdata.mongodb.mongo_positions_by_strategy import mongoStrategyPositionData
from sysdata.mongodb.mongo_historic_orders import (
    mongoBrokerHistoricOrdersData,
    mongoContractHistoricOrdersData,
    mongoStrategyHistoricOrdersData,
)
from sysdata.mongodb.mongo_futures_instruments import mongoFuturesInstrumentData
from sysdata.mongodb.mongo_optimal_position import mongoOptimalPositionData
from sysdata.mongodb.mongo_roll_data import mongoRollParametersData
from sysdata.mongodb.mongo_roll_state_storage import mongoRollStateData

from sysobjects.contracts import futuresContract
from sysobjects.production.tradeable_object import instrumentStrategy

from sysproduction.data.directories import get_csv_backup_directory, get_csv_dump_dir
from sysproduction.data.strategies import get_list_of_strategies

def backup_arctic_to_csv():
    data = dataBlob(log_name="backup_arctic_to_csv")
    backup_object = backupArcticToCsv(data)
    backup_object.backup_arctic_to_csv()

    return None


class backupArcticToCsv:
    def __init__(self, data):
        self.data = data

    def backup_arctic_to_csv(self):
        backup_data = get_data_and_create_csv_directories(self.data.log_name)
        log = self.data.log

        log.msg("Dumping from arctic, mongo to .csv files")
        backup_spreads_to_csv(backup_data)
        backup_fx_to_csv(backup_data)
        backup_futures_contract_prices_to_csv(backup_data)
        backup_multiple_to_csv(backup_data)
        backup_adj_to_csv(backup_data)
        backup_strategy_position_data(backup_data)
        backup_contract_position_data(backup_data)
        backup_historical_orders(backup_data)
        backup_capital(backup_data)
        backup_contract_data(backup_data)
        backup_instrument_data(backup_data)
        backup_optimal_positions(backup_data)
        backup_roll_state_data(backup_data)
        log.msg("Copying to backup directory")
        backup_csv_dump(self.data)


def get_data_and_create_csv_directories(logname):

    csv_dump_dir = get_csv_dump_dir()

    class_paths = dict(
        csvFuturesContractPriceData="contract_prices",
        csvFuturesAdjustedPricesData="adjusted_prices",
        csvFuturesMultiplePricesData="multiple_prices",
        csvFxPricesData="fx_prices",
        csvContractPositionData="contract_positions",
        csvStrategyPositionData="strategy_positions",
        csvBrokerHistoricOrdersData="broker_orders",
        csvContractHistoricOrdersData="contract_orders",
        csvStrategyHistoricOrdersData="strategy_orders",
        csvCapitalData="capital",
        csvFuturesContractData="contracts_data",
        csvFuturesInstrumentData="instrument_data",
        csvOptimalPositionData="optimal_positions",
        csvRollParametersData="roll_parameters",
        csvRollStateData="roll_state",
        csvSpreadsForInstrumentData="spreads",
    )

    for class_name, path in class_paths.items():
        dir_name = os.path.join(csv_dump_dir, path)
        class_paths[class_name] = dir_name
        if not os.path.exists(dir_name):
            os.makedirs(dir_name)

    data = dataBlob(
        csv_data_paths=class_paths, keep_original_prefix=True, log_name=logname
    )

    data.add_class_list(
        [
            csvFuturesContractPriceData,
            csvFuturesAdjustedPricesData,
            csvFuturesMultiplePricesData,
            csvFxPricesData,
            csvContractPositionData,
            csvStrategyPositionData,
            csvBrokerHistoricOrdersData,
            csvContractHistoricOrdersData,
            csvStrategyHistoricOrdersData,
            csvCapitalData,
            csvOptimalPositionData,
            csvFuturesInstrumentData,
            csvRollStateData,
            csvFuturesContractData,
            csvSpreadsForInstrumentData,
        ]
    )

    data.add_class_list(
        [
            arcticFuturesContractPriceData,
            arcticFuturesMultiplePricesData,
            arcticFuturesAdjustedPricesData,
            arcticFxPricesData,
            arcticSpreadsForInstrumentData,
            arcticCapitalData,
            mongoContractPositionData,
            mongoStrategyPositionData,
            mongoBrokerHistoricOrdersData,
            mongoContractHistoricOrdersData,
            mongoStrategyHistoricOrdersData,
            mongoFuturesContractData,
            mongoFuturesInstrumentData,
            mongoOptimalPositionData,
            mongoRollParametersData,
            mongoRollStateData,
        ]
    )

    return data


# Write function for each thing we want to backup
# Think about how to check for duplicates (data frame equals?)


# Futures contract data
def backup_futures_contract_prices_to_csv(data):
    instrument_list = (
        data.arctic_futures_contract_price.get_list_of_instrument_codes_with_merged_price_data()
    )
    for instrument_code in instrument_list:
        backup_futures_contract_prices_for_instrument_to_csv(data, instrument_code)


def backup_futures_contract_prices_for_instrument_to_csv(
    data: dataBlob, instrument_code: str
):
    list_of_contracts = data.arctic_futures_contract_price.contracts_with_merged_price_data_for_instrument_code(
        instrument_code
    )

    for futures_contract in list_of_contracts:
        backup_futures_contract_prices_for_contract_to_csv(data, futures_contract)


def backup_futures_contract_prices_for_contract_to_csv(
        data: dataBlob, futures_contract: futuresContract
        ):
        if futures_contract.days_since_expiry()>CALENDAR_DAYS_IN_YEAR:
            ## Almost certainly expired, skip
            data.log.msg("Skipping expired contract %s" % str(futures_contract))

            return None

        arctic_data = data.arctic_futures_contract_price.get_merged_prices_for_contract_object(
            futures_contract
        )

        csv_data = data.csv_futures_contract_price.get_merged_prices_for_contract_object(
            futures_contract
        )

        if check_df_equals(arctic_data, csv_data):
            # No update needed, move on
            data.log.msg("No prices backup needed for %s" % str(futures_contract))
        else:
            # Write backup
            try:
                data.csv_futures_contract_price.write_merged_prices_for_contract_object(
                    futures_contract,
                    arctic_data,
                    ignore_duplication=True,
                )
                data.log.msg("Written backup .csv of prices for %s" % str(futures_contract))
            except BaseException:
                data.log.warn("Problem writing .csv of prices for %s" % str(futures_contract))


# fx
def backup_fx_to_csv(data):
    fx_codes = data.arctic_fx_prices.get_list_of_fxcodes()
    for fx_code in fx_codes:
        arctic_data = data.arctic_fx_prices.get_fx_prices(fx_code)
        csv_data = data.csv_fx_prices.get_fx_prices(fx_code)
        if check_ts_equals(arctic_data, csv_data):
            data.log.msg("No fx backup needed for %s" % fx_code)
        else:
            # Write backup
            try:
                data.csv_fx_prices.add_fx_prices(
                    fx_code, arctic_data, ignore_duplication=True
                )
                data.log.msg("Written .csv backup for %s" % fx_code)
            except BaseException:
                data.log.warn("Problem writing .csv backup for %s" % fx_code)


def backup_fx_to_csv(data):
    fx_codes = data.arctic_fx_prices.get_list_of_fxcodes()
    for fx_code in fx_codes:
        arctic_data = data.arctic_fx_prices.get_fx_prices(fx_code)
        csv_data = data.csv_fx_prices.get_fx_prices(fx_code)
        if check_ts_equals(arctic_data, csv_data):
            data.log.msg("No fx backup needed for %s" % fx_code)
        else:
            # Write backup
            try:
                data.csv_fx_prices.add_fx_prices(
                    fx_code, arctic_data, ignore_duplication=True
                )
                data.log.msg("Written .csv backup for %s" % fx_code)
            except BaseException:
                data.log.warn("Problem writing .csv backup for %s" % fx_code)


def backup_multiple_to_csv(data):
    instrument_list = data.arctic_futures_multiple_prices.get_list_of_instruments()
    for instrument_code in instrument_list:
        backup_multiple_to_csv_for_instrument(data, instrument_code)


def backup_multiple_to_csv_for_instrument(data, instrument_code: str):
    arctic_data = data.arctic_futures_multiple_prices.get_multiple_prices(
        instrument_code
    )
    csv_data = data.csv_futures_multiple_prices.get_multiple_prices(instrument_code)

    if check_df_equals(arctic_data, csv_data):
        data.log.msg("No multiple prices backup needed for %s" % instrument_code)
        pass
    else:
        try:
            data.csv_futures_multiple_prices.add_multiple_prices(
                instrument_code, arctic_data, ignore_duplication=True
            )
            data.log.msg("Written .csv backup multiple prices for %s" % instrument_code)
        except BaseException:
            data.log.warn(
                "Problem writing .csv backup multiple prices for %s" % instrument_code
            )


def backup_adj_to_csv(data):
    instrument_list = data.arctic_futures_adjusted_prices.get_list_of_instruments()
    for instrument_code in instrument_list:
        backup_adj_to_csv_for_instrument(data, instrument_code)


def backup_adj_to_csv_for_instrument(data: dataBlob, instrument_code: str):
    arctic_data = data.arctic_futures_adjusted_prices.get_adjusted_prices(
        instrument_code
    )
    csv_data = data.csv_futures_adjusted_prices.get_adjusted_prices(instrument_code)

    if check_ts_equals(arctic_data, csv_data):
        data.log.msg("No adjusted prices backup needed for %s" % instrument_code)
        pass
    else:
        try:
            data.csv_futures_adjusted_prices.add_adjusted_prices(
                instrument_code, arctic_data, ignore_duplication=True
            )
            data.log.msg("Written .csv backup for adjusted prices %s" % instrument_code)
        except BaseException:
            data.log.warn(
                "Problem writing .csv backup for adjusted prices %s" % instrument_code
            )


def backup_spreads_to_csv(data: dataBlob):
    instrument_list = data.arctic_spreads_for_instrument.get_list_of_instruments()
    for instrument_code in instrument_list:
        backup_spreads_to_csv_for_instrument(data, instrument_code)


def backup_spreads_to_csv_for_instrument(data: dataBlob, instrument_code: str):
    arctic_data = data.arctic_spreads_for_instrument.get_spreads(instrument_code)
    csv_data = data.csv_spreads_for_instrument.get_spreads(instrument_code)

    if check_ts_equals(arctic_data, csv_data):
        data.log.msg("No spreads backup needed for %s" % instrument_code)
        pass
    else:
        try:
            data.csv_spreads_for_instrument.add_spreads(
                instrument_code, arctic_data, ignore_duplication=True
            )
            data.log.msg("Written .csv backup for spreads %s" % instrument_code)
        except BaseException:
            data.log.warn(
                "Problem writing .csv backup for spreads %s" % instrument_code
            )


def backup_contract_position_data(data):
    instrument_list = (
        data.mongo_contract_position.get_list_of_instruments_with_any_position()
    )
    for instrument_code in instrument_list:
        contract_list = (
            data.mongo_contract_position.get_list_of_contracts_for_instrument_code(
                instrument_code
            )
        )
        for contract in contract_list:
            mongo_data = (
                data.mongo_contract_position.get_position_as_df_for_contract_object(
                    contract
                )
            )
            data.csv_contract_position.write_position_df_for_contract(
                contract, mongo_data
            )
            data.log.msg(
                "Backed up %s %s contract position data" % (instrument_code, contract)
            )


def backup_strategy_position_data(data):
    strategy_list = get_list_of_strategies(data)
    instrument_list = (
        data.mongo_contract_position.get_list_of_instruments_with_any_position()
    )
    for strategy_name in strategy_list:
        for instrument_code in instrument_list:
            instrument_strategy = instrumentStrategy(
                strategy_name=strategy_name, instrument_code=instrument_code
            )
            mongo_data = data.mongo_strategy_position.get_position_as_df_for_instrument_strategy_object(
                instrument_strategy
            )
            if mongo_data is missing_data:
                continue
            data.csv_strategy_position.write_position_df_for_instrument_strategy(
                instrument_strategy, mongo_data
            )
            data.log.msg(
                "Backed up %s %s strategy position data"
                % (instrument_code, strategy_name)
            )


def backup_historical_orders(data):
    data.log.msg("Backing up strategy orders...")
    list_of_orders = [
        data.mongo_strategy_historic_orders.get_order_with_orderid(id)
        for id in data.mongo_strategy_historic_orders.get_list_of_order_ids()
    ]
    data.csv_strategy_historic_orders.write_orders(list_of_orders)
    data.log.msg("Done")

    data.log.msg("Backing up contract orders...")
    list_of_orders = [
        data.mongo_contract_historic_orders.get_order_with_orderid(order_id)
        for order_id in data.mongo_contract_historic_orders.get_list_of_order_ids()
    ]
    data.csv_contract_historic_orders.write_orders(list_of_orders)
    data.log.msg("Done")

    data.log.msg("Backing up broker orders...")
    list_of_orders = [
        data.mongo_broker_historic_orders.get_order_with_orderid(order_id)
        for order_id in data.mongo_broker_historic_orders.get_list_of_order_ids()
    ]
    data.csv_broker_historic_orders.write_orders(list_of_orders)
    data.log.msg("Done")


def backup_capital(data):
    strategy_capital_dict = get_dict_of_strategy_capital(data)
    capital_data_df = add_total_capital_to_strategy_capital_dict_return_df(data, strategy_capital_dict)
    capital_data_df = capital_data_df.ffill()

    data.csv_capital.write_backup_df_of_all_capital(capital_data_df)


def get_dict_of_strategy_capital(data: dataBlob) -> dict:
    strategy_list = get_list_of_strategies(data)
    strategy_capital_data = dict()
    for strategy_name in strategy_list:
        strategy_capital_data[strategy_name] = data.arctic_capital.get_capital_pd_df_for_strategy(
            strategy_name
        )

    return strategy_capital_data

def add_total_capital_to_strategy_capital_dict_return_df(data: dataBlob,
                                          capital_data: dict) -> pd.DataFrame:

    strategy_capital_as_df = pd.concat(capital_data, axis=1)
    total_capital = data.arctic_capital.get_df_of_all_global_capital()
    capital_data = pd.concat([strategy_capital_as_df, total_capital],
                                       axis=1)

    capital_data = capital_data.ffill()

    return  capital_data

def backup_optimal_positions(data):

    strategy_instrument_list = (
        data.mongo_optimal_position.get_list_of_instrument_strategies_with_optimal_position()
    )

    for instrument_strategy in strategy_instrument_list:
        mongo_data = data.mongo_optimal_position.get_optimal_position_as_df_for_instrument_strategy(
            instrument_strategy
        )
        if mongo_data is missing_data:
            continue
        data.csv_optimal_position.write_position_df_for_instrument_strategy(
            instrument_strategy, mongo_data
        )
        data.log.msg("Backed up %s  optimal position data" % str(instrument_strategy))


def backup_instrument_data(data):
    instrument_config = data.mongo_futures_instrument.get_all_instrument_data_as_df()
    data.csv_futures_instrument.write_all_instrument_data_from_df(instrument_config)
    data.log.msg("Backed up instrument config data")


def backup_roll_state_data(data):
    instrument_list = data.mongo_roll_state.get_list_of_instruments()
    roll_state_list = []
    for instrument_code in instrument_list:
        roll_state = data.mongo_roll_state.get_name_of_roll_state(instrument_code)
        roll_state_list.append(roll_state)

    roll_state_df = pd.DataFrame(roll_state_list, index=instrument_list)
    roll_state_df.columns = ["state"]
    data.csv_roll_state.write_all_instrument_data(roll_state_df)
    data.log.msg("Backed up roll state")


def backup_contract_data(data):
    instrument_list = data.mongo_futures_instrument.get_list_of_instruments()
    for instrument_code in instrument_list:
        contract_list = (
            data.mongo_futures_contract.get_all_contract_objects_for_instrument_code(
                instrument_code
            )
        )
        data.csv_futures_contract.write_contract_list_as_df(
            instrument_code, contract_list
        )
        data.log.msg("Backed up contract data for %s" % instrument_code)


def backup_csv_dump(data):
    source_path = get_csv_dump_dir()
    destination_path = get_csv_backup_directory()
    data.log.msg("Copy from %s to %s" % (source_path, destination_path))
    os.system("rsync -av %s %s" % (source_path, destination_path))


if __name__ == '__main__':
    backup_arctic_to_csv()
