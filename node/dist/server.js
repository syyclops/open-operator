"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
const express_1 = __importDefault(require("express"));
const dotenv_1 = __importDefault(require("dotenv"));
dotenv_1.default.config();
const routes_1 = __importDefault(require("./routes"));
const app = (0, express_1.default)();
const errorHandler = (err, req, res, next) => { };
app.use(errorHandler);
app.use(routes_1.default);
exports.default = app;
