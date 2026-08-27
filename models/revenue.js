const mongoose = require("mongoose");

const revenueSchema = new mongoose.Schema(
  {
    parkingLot: {
      type: mongoose.Schema.Types.ObjectId,
      ref: "ParkingLot",
      required: true,
      index: true,
    },

    booking: {
      type: mongoose.Schema.Types.ObjectId,
      ref: "Booking",
    },

    user: {
      type: mongoose.Schema.Types.ObjectId,
      ref: "User",
    },

    amount: {
      type: Number,
      required: true,
      min: 0,
    },

    type: {
      type: String,
      enum: [
        "booking",
        "extension",
        "cancellation",
        "refund",
        "other",
      ],
      required: true,
    },

    paymentStatus: {
      type: String,
      enum: ["pending", "completed", "refunded"],
      default: "completed",
    },

    paymentMethod: {
      type: String,
      enum: ["cash", "upi", "card", "wallet"],
    },

    transactionTime: {
      type: Date,
      default: Date.now,
      index: true,
    },
  },
  {
    timestamps: true,
  }
);

revenueSchema.index({
  parkingLot: 1,
  transactionTime: -1,
});

module.exports = mongoose.model("Revenue", revenueSchema);