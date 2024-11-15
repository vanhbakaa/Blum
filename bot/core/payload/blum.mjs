import { Blum } from './gen2.mjs';
const [gameId, pointsArg, freezeArg] = process.argv.slice(2);

const points = parseInt(pointsArg, 10);
const freeze = parseInt(freezeArg, 10);

const challenge = Blum.getChallenge(gameId);
const uuidChallenge = Blum.getUUID();

const challengeData = {
    id: uuidChallenge,
    nonce: challenge.nonce,
    hash: challenge.hash,
};

const earnedPoints = {
    BP: {
        amount: points,
    },
};

const assetClicks = {
    CLOVER: {
        clicks: points,
    },
    FREEZE: {
        clicks: freeze,
    },
    BOMB: {
        clicks: 0,
    },
};

const payload = Blum.getPayload(gameId, challengeData, earnedPoints, assetClicks);

console.log(payload);
