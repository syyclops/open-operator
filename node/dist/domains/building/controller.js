"use strict";
var __awaiter = (this && this.__awaiter) || function (thisArg, _arguments, P, generator) {
    function adopt(value) { return value instanceof P ? value : new P(function (resolve) { resolve(value); }); }
    return new (P || (P = Promise))(function (resolve, reject) {
        function fulfilled(value) { try { step(generator.next(value)); } catch (e) { reject(e); } }
        function rejected(value) { try { step(generator["throw"](value)); } catch (e) { reject(e); } }
        function step(result) { result.done ? resolve(result.value) : adopt(result.value).then(fulfilled, rejected); }
        step((generator = generator.apply(thisArg, _arguments || [])).next());
    });
};
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.getBuilding = void 0;
const neo4j_driver_1 = __importDefault(require("../../config/neo4j_driver"));
const getBuilding = (uri) => __awaiter(void 0, void 0, void 0, function* () {
    const session = neo4j_driver_1.default.session();
    try {
        const result = yield session.run(`MATCH (b:Building {uri: $uri}) return b`, {
            uri: uri,
        });
        const singleRecord = result.records[0];
        const node = singleRecord.get(0);
        const building = node.properties;
        console.log(building);
        return building;
    }
    finally {
        yield session.close();
    }
});
exports.getBuilding = getBuilding;
