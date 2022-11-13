"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
const express_1 = require("express");
const controller_1 = require("./controller");
const router = (0, express_1.Router)();
const multer_1 = __importDefault(require("multer"));
var upload = (0, multer_1.default)({ dest: 'uploads/' });
router.post('/uploadIfc', upload.single('ifc'), (req, res) => {
    try {
        const ifc = req.file;
        console.log(ifc);
        (0, controller_1.convertIfcToBrickModel)(ifc);
        // remove from disk
        // fs.unlink(ifc!.path, (err) => console.error(err))
        res.json({
            status: 'SUCCESS',
            data: '',
        });
    }
    catch (err) {
        res.json({
            status: 'FAILED',
            message: err.message,
        });
    }
});
exports.default = router;
