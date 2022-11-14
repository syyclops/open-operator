"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
const port = process.env.PORT || 3000;
const createExpressApp_1 = __importDefault(require("./app/createExpressApp"));
createExpressApp_1.default.get('/', (req, res) => res.send({ hello: 'world' }));
createExpressApp_1.default.listen(port, () => {
    console.log(`Server running on port ${port}`);
});
