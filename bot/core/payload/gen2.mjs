import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import { parentPort } from 'worker_threads';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const self = global;

"use strict";

const globalScope = globalThis || void 0 || self;
let wasmExports;

const heap = new Array(128).fill(undefined);
heap.push(undefined, null, true, false);

function getObject(idx) {
    return heap[idx];
}

let WASM_VECTOR_LEN = 0;
let cacheUint8Memory = null;

function getUint8Memory() {
    if (cacheUint8Memory === null || cacheUint8Memory.byteLength === 0) {
        cacheUint8Memory = new Uint8Array(wasmExports.memory.buffer);
    }
    return cacheUint8Memory;
}

const textEncoder = typeof TextEncoder !== "undefined" ? new TextEncoder("utf-8") : {
    encode: () => {
        throw Error("TextEncoder not available");
    }
};

const encodeString = typeof textEncoder.encodeInto === "function"
    ? function (arg, view) {
        return textEncoder.encodeInto(arg, view);
    }
    : function (arg, view) {
        const buf = textEncoder.encode(arg);
        view.set(buf);
        return {
            read: arg.length,
            written: buf.length
        };
    };

function passStringToWasm(arg, malloc, realloc) {
    if (realloc === undefined) {
        const buf = textEncoder.encode(arg);
        const ptr = malloc(buf.length, 1) >>> 0;
        getUint8Memory().subarray(ptr, ptr + buf.length).set(buf);
        WASM_VECTOR_LEN = buf.length;
        return ptr;
    }

    let len = arg.length;
    let ptr = malloc(len, 1) >>> 0;

    const mem = getUint8Memory();

    let offset = 0;

    for (; offset < len; offset++) {
        const code = arg.charCodeAt(offset);
        if (code > 127) break;
        mem[ptr + offset] = code;
    }

    if (offset !== len) {
        if (offset !== 0) arg = arg.slice(offset);
        ptr = realloc(ptr, len, len = offset + arg.length * 3, 1) >>> 0;
        const view = getUint8Memory().subarray(ptr + offset, ptr + len);
        const ret = encodeString(arg, view);
        offset += ret.written;
        ptr = realloc(ptr, len, offset, 1) >>> 0;
    }

    WASM_VECTOR_LEN = offset;
    return ptr;
}

function isNullish(x) {
    return x == null;
}

let cacheDataView = null;

function getDataView() {
    if (
        cacheDataView === null ||
        cacheDataView.buffer.detached === true ||
        (cacheDataView.buffer.detached === undefined && cacheDataView.buffer !== wasmExports.memory.buffer)
    ) {
        cacheDataView = new DataView(wasmExports.memory.buffer);
    }
    return cacheDataView;
}

let heapNext = heap.length;

function dropObject(idx) {
    if (idx < 132) return;
    heap[idx] = heapNext;
    heapNext = idx;
}

function takeObject(idx) {
    const ret = getObject(idx);
    dropObject(idx);
    return ret;
}

const textDecoder = typeof TextDecoder !== "undefined" ? new TextDecoder("utf-8", {
    ignoreBOM: true,
    fatal: true
}) : {
    decode: () => {
        throw Error("TextDecoder not available");
    }
};

if (typeof TextDecoder !== "undefined") {
    textDecoder.decode();
}

function getStringFromWasm(ptr, len) {
    ptr = ptr >>> 0;
    return textDecoder.decode(getUint8Memory().subarray(ptr, ptr + len));
}

function addHeapObject(obj) {
    if (heapNext === heap.length) heap.push(heap.length + 1);
    const idx = heapNext;
    heapNext = heap[idx];
    heap[idx] = obj;
    return idx;
}

function debugString(val) {
    const type = typeof val;
    if (type == "number" || type == "boolean" || val == null) {
        return `${val}`;
    }
    if (type == "string") {
        return `"${val}"`;
    }
    if (type == "symbol") {
        const description = val.description;
        return description == null ? "Symbol" : `Symbol(${description})`;
    }
    if (type == "function") {
        const name = val.name;
        return typeof name == "string" && name.length > 0 ? `Function(${name})` : "Function";
    }
    if (Array.isArray(val)) {
        const length = val.length;
        let debug = "[";
        if (length > 0) debug += debugString(val[0]);
        for (let i = 1; i < length; i++) {
            debug += ", " + debugString(val[i]);
        }
        debug += "]";
        return debug;
    }
    const builtInMatches = /\[object ([^\]]+)\]/.exec(toString.call(val));
    let className;
    if (builtInMatches.length > 1) {
        className = builtInMatches[1];
    } else {
        return toString.call(val);
    }
    if (className == "Object") {
        try {
            return "Object(" + JSON.stringify(val) + ")";
        } catch (_) {
            return "Object";
        }
    }
    if (val instanceof Error) {
        return `${val.name}: ${val.message}\n${val.stack}`;
    }
    return className;
}

function getChallenge(input) {
    try {
        const retptr = wasmExports.__wbindgen_add_to_stack_pointer(-16);
        const ptr0 = passStringToWasm(input, wasmExports.__wbindgen_malloc, wasmExports.__wbindgen_realloc);
        const len0 = WASM_VECTOR_LEN;
        wasmExports.proof(retptr, ptr0, len0);
        var r0 = getDataView().getInt32(retptr + 0 * 4, true);
        var r1 = getDataView().getInt32(retptr + 1 * 4, true);
        var r2 = getDataView().getInt32(retptr + 2 * 4, true);
        if (r2) throw takeObject(r1);
        return takeObject(r0);
    } finally {
        wasmExports.__wbindgen_add_to_stack_pointer(16);
    }
}

function getPayload(gameId, challenge, earnedPoints, assetClicks) {
    let ptr1, len1;
    try {
        const retptr = wasmExports.__wbindgen_add_to_stack_pointer(-16);
        const ptr0 = passStringToWasm(gameId, wasmExports.__wbindgen_malloc, wasmExports.__wbindgen_realloc);
        const len0 = WASM_VECTOR_LEN;
        wasmExports.pack(retptr, ptr0, len0, addHeapObject(challenge), addHeapObject(earnedPoints), addHeapObject(assetClicks));
        var r0 = getDataView().getInt32(retptr + 0 * 4, true);
        var r1 = getDataView().getInt32(retptr + 1 * 4, true);
        var r2 = getDataView().getInt32(retptr + 2 * 4, true);
        var r3 = getDataView().getInt32(retptr + 3 * 4, true);
        ptr1 = r0;
        len1 = r1;
        if (r3) throw (ptr1 = 0, len1 = 0, takeObject(r2));
        return getStringFromWasm(ptr1, len1);
    } finally {
        wasmExports.__wbindgen_add_to_stack_pointer(16);
        wasmExports.__wbindgen_free(ptr1, len1, 1);
    }
}

function handleError(fn, args) {
    try {
        return fn.apply(this, args);
    } catch (e) {
        wasmExports.__wbindgen_exn_store(addHeapObject(e));
    }
}

async function loadWebAssembly(module, imports) {
    if (typeof Response === "function" && module instanceof Response) {
        if (typeof WebAssembly.instantiateStreaming === "function") {
            try {
                return await WebAssembly.instantiateStreaming(module, imports);
            } catch (e) {
                if (module.headers.get("Content-Type") != "application/wasm") {
                    console.warn(
                        "`WebAssembly.instantiateStreaming` failed because your server does not serve wasm with `application/wasm` MIME type. Falling back to `WebAssembly.instantiate` which is slower. Original error:\n",
                        e
                    );
                } else {
                    throw e;
                }
            }
        }
        const bytes = await module.arrayBuffer();
        return await WebAssembly.instantiate(bytes, imports);
    } else {
        const instance = await WebAssembly.instantiate(module, imports);
        if (instance instanceof WebAssembly.Instance) {
            return { instance, module };
        } else {
            return instance;
        }
    }
}

function getImports() {
    const imports = {};
    imports.wbg = {};
    imports.wbg.__wbindgen_string_get = function (arg0, arg1) {
        const obj = getObject(arg1);
        const ret = typeof obj === "string" ? obj : undefined;
        var ptr0 = isNullish(ret) ? 0 : passStringToWasm(ret, wasmExports.__wbindgen_malloc, wasmExports.__wbindgen_realloc);
        var len0 = WASM_VECTOR_LEN;
        getDataView().setInt32(arg0 + 1 * 4, len0, true);
        getDataView().setInt32(arg0 + 0 * 4, ptr0, true);
    };
    imports.wbg.__wbindgen_object_drop_ref = function (arg0) {
        takeObject(arg0);
    };
    imports.wbg.__wbindgen_error_new = function (arg0, arg1) {
        const ret = new Error(getStringFromWasm(arg0, arg1));
        return addHeapObject(ret);
    };
    imports.wbg.__wbindgen_is_bigint = function (arg0) {
        const ret = typeof getObject(arg0) === "bigint";
        return ret;
    };
    imports.wbg.__wbindgen_bigint_from_u64 = function (arg0) {
        const ret = BigInt.asUintN(64, arg0);
        return addHeapObject(ret);
    };
    imports.wbg.__wbindgen_jsval_eq = function (arg0, arg1) {
        const ret = getObject(arg0) === getObject(arg1);
        return ret;
    };
    imports.wbg.__wbindgen_is_object = function (arg0) {
        const val = getObject(arg0);
        const ret = typeof val === "object" && val !== null;
        return ret;
    };
    imports.wbg.__wbindgen_is_undefined = function (arg0) {
        const ret = getObject(arg0) === undefined;
        return ret;
    };
    imports.wbg.__wbindgen_in = function (arg0, arg1) {
        const ret = getObject(arg0) in getObject(arg1);
        return ret;
    };
    imports.wbg.__wbg_crypto_1d1f22824a6a080c = function (arg0) {
        const ret = getObject(arg0).crypto;
        return addHeapObject(ret);
    };
    imports.wbg.__wbg_process_4a72847cc503995b = function (arg0) {
        const ret = getObject(arg0).process;
        return addHeapObject(ret);
    };
    imports.wbg.__wbg_versions_f686565e586dd935 = function (arg0) {
        const ret = getObject(arg0).versions;
        return addHeapObject(ret);
    };
    imports.wbg.__wbg_node_104a2ff8d6ea03a2 = function (arg0) {
        const ret = getObject(arg0).node;
        return addHeapObject(ret);
    };
    imports.wbg.__wbindgen_is_string = function (arg0) {
        const ret = typeof getObject(arg0) === "string";
        return ret;
    };
    imports.wbg.__wbg_require_cca90b1a94a0255b = function () {
        return handleError(function () {
            const ret = module.require;
            return addHeapObject(ret);
        }, arguments);
    };
    imports.wbg.__wbindgen_is_function = function (arg0) {
        const ret = typeof getObject(arg0) === "function";
        return ret;
    };
    imports.wbg.__wbindgen_string_new = function (arg0, arg1) {
        const ret = getStringFromWasm(arg0, arg1);
        return addHeapObject(ret);
    };
    imports.wbg.__wbg_msCrypto_eb05e62b530a1508 = function (arg0) {
        const ret = getObject(arg0).msCrypto;
        return addHeapObject(ret);
    };
    imports.wbg.__wbg_randomFillSync_5c9c955aa56b6049 = function () {
        return handleError(function (arg0, arg1) {
            getObject(arg0).randomFillSync(takeObject(arg1));
        }, arguments);
    };
    imports.wbg.__wbg_getRandomValues_3aa56aa6edec874c = function () {
        return handleError(function (arg0, arg1) {
            getObject(arg0).getRandomValues(getObject(arg1));
        }, arguments);
    };
    imports.wbg.__wbindgen_jsval_loose_eq = function (arg0, arg1) {
        const ret = getObject(arg0) == getObject(arg1);
        return ret;
    };
    imports.wbg.__wbindgen_boolean_get = function (arg0) {
        const v = getObject(arg0);
        const ret = typeof v === "boolean" ? (v ? 1 : 0) : 2;
        return ret;
    };
    imports.wbg.__wbindgen_number_get = function (arg0, arg1) {
        const obj = getObject(arg1);
        const ret = typeof obj === "number" ? obj : undefined;
        getDataView().setFloat64(arg0 + 8, isNullish(ret) ? 0 : ret, true);
        getDataView().setInt32(arg0 + 0, !isNullish(ret), true);
    };
    imports.wbg.__wbindgen_as_number = function (arg0) {
        const ret = +getObject(arg0);
        return ret;
    };
    imports.wbg.__wbindgen_number_new = function (arg0) {
        const ret = arg0;
        return addHeapObject(ret);
    };
    imports.wbg.__wbindgen_object_clone_ref = function (arg0) {
        const ret = getObject(arg0);
        return addHeapObject(ret);
    };
    imports.wbg.__wbg_getwithrefkey_edc2c8960f0f1191 = function (arg0, arg1) {
        const ret = getObject(arg0)[getObject(arg1)];
        return addHeapObject(ret);
    };
    imports.wbg.__wbg_set_f975102236d3c502 = function (arg0, arg1, arg2) {
        getObject(arg0)[takeObject(arg1)] = takeObject(arg2);
    };
    imports.wbg.__wbg_String_b9412f8799faab3e = function (arg0, arg1) {
        const ret = String(getObject(arg1));
        const ptr0 = passStringToWasm(ret, wasmExports.__wbindgen_malloc, wasmExports.__wbindgen_realloc);
        const len0 = WASM_VECTOR_LEN;
        getDataView().setInt32(arg0 + 4, len0, true);
        getDataView().setInt32(arg0 + 0, ptr0, true);
    };
    imports.wbg.__wbg_get_3baa728f9d58d3f6 = function (arg0, arg1) {
        const ret = getObject(arg0)[arg1 >>> 0];
        return addHeapObject(ret);
    };
    imports.wbg.__wbg_length_ae22078168b726f5 = function (arg0) {
        const ret = getObject(arg0).length;
        return ret;
    };
    imports.wbg.__wbg_newnoargs_76313bd6ff35d0f2 = function (arg0, arg1) {
        const ret = new Function(getStringFromWasm(arg0, arg1));
        return addHeapObject(ret);
    };
    imports.wbg.__wbg_next_de3e9db4440638b2 = function (arg0) {
        const ret = getObject(arg0).next;
        return addHeapObject(ret);
    };
    imports.wbg.__wbg_next_f9cb570345655b9a = function () {
        return handleError(function (arg0) {
            const ret = getObject(arg0).next();
            return addHeapObject(ret);
        }, arguments);
    };
    imports.wbg.__wbg_done_bfda7aa8f252b39f = function (arg0) {
        const ret = getObject(arg0).done;
        return ret;
    };
    imports.wbg.__wbg_value_6d39332ab4788d86 = function (arg0) {
        const ret = getObject(arg0).value;
        return addHeapObject(ret);
    };
    imports.wbg.__wbg_iterator_888179a48810a9fe = function () {
        const ret = Symbol.iterator;
        return addHeapObject(ret);
    };
    imports.wbg.__wbg_get_224d16597dbbfd96 = function () {
        return handleError(function (arg0, arg1) {
            const ret = Reflect.get(getObject(arg0), getObject(arg1));
            return addHeapObject(ret);
        }, arguments);
    };
    imports.wbg.__wbg_call_1084a111329e68ce = function () {
        return handleError(function (arg0, arg1) {
            const ret = getObject(arg0).call(getObject(arg1));
            return addHeapObject(ret);
        }, arguments);
    };
    imports.wbg.__wbg_new_525245e2b9901204 = function () {
        const ret = new Object();
        return addHeapObject(ret);
    };
    imports.wbg.__wbg_self_3093d5d1f7bcb682 = function () {
        return handleError(function () {
            const ret = self.self;
            return addHeapObject(ret);
        }, arguments);
    };
    imports.wbg.__wbg_window_3bcfc4d31bc012f8 = function () {
        return handleError(function () {
            const ret = window.window;
            return addHeapObject(ret);
        }, arguments);
    };
    imports.wbg.__wbg_globalThis_86b222e13bdf32ed = function () {
        return handleError(function () {
            const ret = globalThis.globalThis;
            return addHeapObject(ret);
        }, arguments);
    };
    imports.wbg.__wbg_global_e5a3fe56f8be9485 = function () {
        return handleError(function () {
            const ret = globalScope.global;
            return addHeapObject(ret);
        }, arguments);
    };
    imports.wbg.__wbg_instanceof_ArrayBuffer_61dfc3198373c902 = function (arg0) {
        let result;
        try {
            result = getObject(arg0) instanceof ArrayBuffer;
        } catch {
            result = false;
        }
        const ret = result;
        return ret;
    };
    imports.wbg.__wbg_call_89af060b4e1523f2 = function () {
        return handleError(function (arg0, arg1, arg2) {
            const ret = getObject(arg0).call(getObject(arg1), getObject(arg2));
            return addHeapObject(ret);
        }, arguments);
    };
    imports.wbg.__wbg_isSafeInteger_7f1ed56200d90674 = function (arg0) {
        const ret = Number.isSafeInteger(getObject(arg0));
        return ret;
    };
    imports.wbg.__wbg_entries_7a0e06255456ebcd = function (arg0) {
        const ret = Object.entries(getObject(arg0));
        return addHeapObject(ret);
    };
    imports.wbg.__wbg_buffer_b7b08af79b0b0974 = function (arg0) {
        const ret = getObject(arg0).buffer;
        return addHeapObject(ret);
    };
    imports.wbg.__wbg_newwithbyteoffsetandlength_8a2cb9ca96b27ec9 = function (arg0, arg1, arg2) {
        const ret = new Uint8Array(getObject(arg0), arg1 >>> 0, arg2 >>> 0);
        return addHeapObject(ret);
    };
    imports.wbg.__wbg_new_ea1883e1e5e86686 = function (arg0) {
        const ret = new Uint8Array(getObject(arg0));
        return addHeapObject(ret);
    };
    imports.wbg.__wbg_set_d1e79e2388520f18 = function (arg0, arg1, arg2) {
        getObject(arg0).set(getObject(arg1), arg2 >>> 0);
    };
    imports.wbg.__wbg_length_8339fcf5d8ecd12e = function (arg0) {
        const ret = getObject(arg0).length;
        return ret;
    };
    imports.wbg.__wbg_instanceof_Uint8Array_247a91427532499e = function (arg0) {
        let result;
        try {
            result = getObject(arg0) instanceof Uint8Array;
        } catch {
            result = false;
        }
        const ret = result;
        return ret;
    };
    imports.wbg.__wbg_newwithlength_ec548f448387c968 = function (arg0) {
        const ret = new Uint8Array(arg0 >>> 0);
        return addHeapObject(ret);
    };
    imports.wbg.__wbg_subarray_7c2e3576afe181d1 = function (arg0, arg1, arg2) {
        const ret = getObject(arg0).subarray(arg1 >>> 0, arg2 >>> 0);
        return addHeapObject(ret);
    };
    imports.wbg.__wbindgen_bigint_get_as_i64 = function (arg0, arg1) {
        const v = getObject(arg1);
        const ret = typeof v === "bigint" ? v : undefined;
        getDataView().setBigInt64(arg0 + 8, isNullish(ret) ? BigInt(0) : ret, true);
        getDataView().setInt32(arg0 + 0, !isNullish(ret), true);
    };
    imports.wbg.__wbindgen_debug_string = function (arg0, arg1) {
        const ret = debugString(getObject(arg1));
        const ptr0 = passStringToWasm(ret, wasmExports.__wbindgen_malloc, wasmExports.__wbindgen_realloc);
        const len0 = WASM_VECTOR_LEN;
        getDataView().setInt32(arg0 + 4, len0, true);
        getDataView().setInt32(arg0 + 0, ptr0, true);
    };
    imports.wbg.__wbindgen_throw = function (arg0, arg1) {
        throw new Error(getStringFromWasm(arg0, arg1));
    };
    imports.wbg.__wbindgen_memory = function () {
        const ret = wasmExports.memory;
        return addHeapObject(ret);
    };
    return imports;
}

function initWasm(instance, module) {
    wasmExports = instance.exports;
    initWasm.__wbindgen_wasm_module = module;
    cacheDataView = null;
    cacheUint8Memory = null;
    return wasmExports;
}

async function initializeWasm() {
    if (wasmExports !== undefined) return wasmExports;
    const module = fs.readFileSync(path.resolve(__dirname, './blum_wasm.wasm'));
    const imports = getImports();
    const { instance, module: wasmModule } = await loadWebAssembly(module, imports);
    return initWasm(instance, wasmModule);
}

let wasmInitPromise;

const ensureWasmInitialized = async () => {
    if (wasmInitPromise === undefined) {
        wasmInitPromise = initializeWasm();
    }
    await wasmInitPromise;
};

self.onmessage = async event => {
    await ensureWasmInitialized();
    const { id, method, payload } = event.data;
    switch (method) {
        case "proof": {
            const result = getChallenge(payload);
            return self.postMessage({
                id,
                ...result
            });
        }
        case "pack": {
            const hash = getPayload(payload.gameId, payload.challenge, payload.earnedPoints, payload.assetClicks);
            return self.postMessage({
                id,
                hash
            });
        }
        default: {
            throw new Error(`Unknown method: ${method}`);
        }
    }
};

function generateUUID() {
    return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, c => {
        const r = (Math.random() * 16) | 0;
        return (c === 'x' ? r : ((r & 0x3) | 0x8)).toString(16);
    });
}

export const Blum = {
    getUUID: generateUUID,
    getChallenge,
    getPayload,
    init: initializeWasm,
};

await Blum.init();
