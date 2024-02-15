import * as functions from "firebase-functions";
import * as admin from "firebase-admin";
import {connectMongoDB} from "./mongodb";

export const likeRecipe = functions.https.onCall(async (data, context) => {
  // Check if the user is authenticated
  if (!context.auth) {
    throw new functions.https.HttpsError(
      "unauthenticated",
      "The user must be authenticated to like a recipe.",
    );
  }

  const userId = context.auth.uid;
  const recipeId = data.recipeId;

  if (!userId || !recipeId) {
    throw new functions.https.HttpsError(
      "invalid-argument",
      "The function must be called with both userId and recipeId arguments.",
    );
  }

  const databaseName = "WellnessDatabase";
  const collectionName = "Recipes";

  const mongoClient = await connectMongoDB();

  const db = mongoClient.db(databaseName);

  const recipeCollection = db.collection(collectionName);

  const recipeExists = recipeCollection.findOne({id: recipeId});

  if (!recipeExists) {
    throw new functions.https.HttpsError(
      "not-found",
      "Recipe not found in MongoDB.",
    );
  }

  // Unique document ID from userId and recipeId
  const likeId = `${userId}_${recipeId}`;

  // Save the like in Firestore
  try {
    await admin.firestore().collection("likes").doc(likeId).set({
      userId: userId,
      recipeId: recipeId,
      createdAt: admin.firestore.FieldValue.serverTimestamp(),
    });
    return {success: true, message: "Like saved successfully"};
  } catch (error) {
    console.error("Error saving like:", error);
    throw new functions.https.HttpsError(
      "unknown",
      "Failed to save like",
      error,
    );
  } finally {
    // Always disconnect the MongoDB client
    await mongoClient.close();
  }
});

// USE ID FROM USER CONTEXT DO NOT SEND IT

export const unlikeRecipe = functions.https.onCall(async (data, context) => {
  if (!context.auth) {
    throw new functions.https.HttpsError(
      "unauthenticated",
      "The user must be authenticated to delete a like.",
    );
  }

  const userId = context.auth.uid;
  const {recipeId} = data;

  if (!recipeId) {
    throw new functions.https.HttpsError(
      "invalid-argument",
      "The function must be called with a recipeId argument.",
    );
  }

  const likesCollection = admin.firestore().collection("likes");
  const snapshot = await likesCollection
    .where("userId", "==", userId)
    .where("recipeId", "==", recipeId)
    .limit(1)
    .get();

  if (snapshot.empty) {
    throw new functions.https.HttpsError("not-found", "Like not found.");
  }

  // Assuming only one like per user per recipe is allowed
  await likesCollection.doc(snapshot.docs[0].id).delete();

  return {success: true, message: "Like deleted successfully"};
});

export const recipeIsLiked = functions.https.onCall(async (data, context) => {
  // Check if the user is authenticated
  if (!context.auth) {
    throw new functions.https.HttpsError(
      "unauthenticated",
      "The user must be authenticated to check likes.",
    );
  }

  const userId = context.auth.uid;
  const {recipeId} = data;

  // Validate input
  if (!userId || !recipeId) {
    throw new functions.https.HttpsError(
      "invalid-argument",
      "The function must be called with both userId and recipeId arguments.",
    );
  }

  try {
    const likesRef = admin.firestore().collection("likes");
    const snapshot = await likesRef
      .where("userId", "==", userId)
      .where("recipeId", "==", recipeId)
      .limit(1)
      .get();

    if (snapshot.empty) {
      return {isLiked: false};
    } else {
      // Assuming there can only be one like per user per recipe,
      // if a document is found, then the recipe is liked by the user.
      return {isLiked: true};
    }
  } catch (error) {
    console.error("Error checking like status:", error);
    throw new functions.https.HttpsError(
      "unknown",
      "Failed to check like status",
      error,
    );
  }
});

export const getUserLikedRecipes = functions.https.onCall(
  async (data, context) => {
    if (!context.auth) {
      throw new functions.https.HttpsError(
        "unauthenticated",
        "The user must be authenticated to fetch liked recipes.",
      );
    }

    const userId = context.auth.uid;
    try {
      const likesSnapshot = await admin
        .firestore()
        .collection("likes")
        .where("userId", "==", userId)
        .get();
      const recipeIds = likesSnapshot.docs.map((doc) => doc.data().recipeId);

      const mongoClient = await connectMongoDB();
      const db = mongoClient.db("WellnessDatabase");
      const recipeCollection = db.collection("Recipes");

      const recipes = await recipeCollection
        .find(
          {
            id: {$in: recipeIds},
          },
          {
            projection: {
              name: 1,
              description: 1,
              image: 1,
              rating: 1,
              nutritional_score: 1,
              protein_score: 1,
              id: 1,
            },
          },
        )
        .toArray();

      return recipes;
    } catch (error) {
      console.error("Error fetching user likes:", error);
      throw new functions.https.HttpsError(
        "unknown",
        "Failed to fetch user likes",
        error,
      );
    }
  },
);
