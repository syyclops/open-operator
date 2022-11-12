"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
const neo4j_driver_1 = __importDefault(require("neo4j-driver"));
const dotenv_1 = __importDefault(require("dotenv"));
dotenv_1.default.config();
const driver = neo4j_driver_1.default.driver(process.env.NEO4J_URL, neo4j_driver_1.default.auth.basic(process.env.NEO4J_USER, process.env.NEO4J_PASS));
exports.default = driver;
